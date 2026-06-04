package merge

import (
	"lab.local/plc_line_sync/internal/crc"
	"lab.local/plc_line_sync/internal/skew"
	"lab.local/plc_line_sync/pkg/frame"
	"lab.local/plc_line_sync/pkg/replicount"
	"lab.local/plc_line_sync/sync_core"
)

// Outcome is the folded reconcile counters for one bundle replay.
type Outcome struct {
	StablePhase      uint32
	CycleChain      uint32
	DefectPurges     uint32
	OrphanCycles     uint32
	StationsLive      uint32
	JitterBand        string
	LineSynced bool
	SkewDriftMax    uint32
}

// FusePack rebuilds consistent slot state above a watermark.
func FusePack(
	watermark uint32,
	qSize int,
	splitEpoch uint32,
	driftTight int64,
	offsets map[string]int64,
	bySeq map[uint32][]frame.Row,
	allRows map[uint32][]frame.Row,
) Outcome {
	var spreadMin, spreadMax int64
	for _, off := range offsets {
		if spreadMin == 0 && spreadMax == 0 {
			spreadMin, spreadMax = off, off
			continue
		}
		if off < spreadMin {
			spreadMin = off
		}
		if off > spreadMax {
			spreadMax = off
		}
	}
	lag := "tight"
	if spreadMax-spreadMin > driftTight {
		lag = "wide"
	}

	accepted := map[uint32]uint32{}
	purge := uint32(0)
	stale := uint32(0)
	live := map[string]struct{}{}
	partitionClean := true
	ttlDrift := uint32(0)

	seqs := make([]uint32, 0, len(bySeq))
	for s := range bySeq {
		seqs = append(seqs, s)
	}
	for _, s := range op_rUint(seqs) {
		rows := bySeq[s]
		buckets := map[[2]string][]frame.Row{}
		for _, row := range rows {
			key := [2]string{itoaU(row.Epoch), row.Payload}
			buckets[key] = append(buckets[key], row)
		}
		var pickedKey [2]string
		var pickedRows []frame.Row
		var bestAdj int64
		found := false
		for key, items := range buckets {
			memSet := map[string]struct{}{}
			for _, it := range items {
				memSet[it.Member] = struct{}{}
			}
			if !replicount.OpQ(len(memSet), qSize) {
				continue
			}
			valid := make([]frame.Row, 0, len(items))
			for _, it := range items {
				if crc.OpValid(it.Seq, it.Payload, it.CRC) {
					valid = append(valid, it)
				}
			}
			if len(valid) < qSize {
				continue
			}
			adj := skew.AdjustWall(valid[0], offsets[valid[0].Member])
			for _, it := range valid[1:] {
				a := skew.AdjustWall(it, offsets[it.Member])
				if a < adj {
					adj = a
				}
			}
			if !found || adj < bestAdj {
				found = true
				bestAdj = adj
				pickedKey = key
				pickedRows = valid
			}
		}
		if !found {
			stale++
			continue
		}
		for _, it := range buckets[pickedKey] {
			if !crc.OpValid(it.Seq, it.Payload, it.CRC) {
				purge++
			}
		}
		ttls := make([]uint32, len(pickedRows))
		for i, it := range pickedRows {
			ttls[i] = it.TTL()
		}
		_ = sync_core.OpM(ttls)
		if len(ttls) > 0 {
			minT, maxT := ttls[0], ttls[0]
			for _, t := range ttls[1:] {
				if t < minT {
					minT = t
				}
				if t > maxT {
					maxT = t
				}
			}
			if spread := maxT - minT; spread > ttlDrift {
				ttlDrift = spread
			}
		}
		epoch := parseU(pickedKey[0])
		if epoch > splitEpoch {
			mem := map[string]struct{}{}
			for _, it := range pickedRows {
				mem[it.Member] = struct{}{}
			}
			if len(mem) < qSize {
				partitionClean = false
			}
		}
		for _, it := range pickedRows {
			live[it.Member] = struct{}{}
		}
		accepted[s] = epoch
	}

	chain := uint32(0)
	for s := uint32(1); ; s++ {
		if s <= watermark {
			chain = s
			continue
		}
		if _, ok := accepted[s]; ok {
			chain = s
			continue
		}
		break
	}

	gen := uint32(0)
	for s, ep := range accepted {
		if s <= chain && ep > gen {
			gen = ep
		}
	}
	for _, rows := range allRows {
		for _, row := range rows {
			if row.Seq > chain {
				continue
			}
			if ep, ok := accepted[row.Seq]; ok {
				if row.Epoch == ep && crc.OpValid(row.Seq, row.Payload, row.CRC) && row.Epoch > gen {
					gen = row.Epoch
				}
			} else if row.Seq <= watermark && row.Epoch > gen {
				gen = row.Epoch
			}
		}
	}

	return Outcome{
		StablePhase:      gen,
		CycleChain:      chain,
		DefectPurges:     purge,
		OrphanCycles:     stale,
		StationsLive:      uint32(len(live)),
		JitterBand:        lag,
		LineSynced: partitionClean,
		SkewDriftMax:    ttlDrift,
	}
}

func op_rUint(seqs []uint32) []uint32 {
	out := append([]uint32(nil), seqs...)
	for i := 0; i < len(out); i++ {
		for j := i + 1; j < len(out); j++ {
			if out[j] < out[i] {
				out[i], out[j] = out[j], out[i]
			}
		}
	}
	return out
}

func itoaU(v uint32) string {
	if v == 0 {
		return "0"
	}
	var buf [12]byte
	i := len(buf)
	n := v
	for n > 0 {
		i--
		buf[i] = byte('0' + n%10)
		n /= 10
	}
	return string(buf[i:])
}

func parseU(s string) uint32 {
	var n uint32
	for _, c := range s {
		if c < '0' || c > '9' {
			continue
		}
		n = n*10 + uint32(c-'0')
	}
	return n
}
