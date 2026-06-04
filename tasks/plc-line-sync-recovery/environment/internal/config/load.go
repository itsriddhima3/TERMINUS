package config

import (
	"encoding/json"
	"os"
	"path/filepath"

	"lab.local/plc_line_sync/pkg/frame"
	"lab.local/plc_line_sync/pkg/member"
)

// Pack describes one assembly line PLC snapshot.
type Pack struct {
	PackID       string   `json:"pack_id"`
	LineID     string   `json:"line_id"`
	QSize        int      `json:"q_size"`
	SplitEpoch   uint32   `json:"split_epoch"`
	SplitGen     uint32   `json:"split_gen"`
	DriftTightMS int64    `json:"drift_tight_ms"`
	LagTightMS   int64    `json:"lag_tight_ms"`
	TrustAnchor  string   `json:"trust_anchor"`
	Members      []string `json:"stations"`
	Nodes        []string `json:"nodes"`
}

func (p Pack) ID() string {
	if p.LineID != "" {
		return p.LineID
	}
	return p.PackID
}

func (p Pack) Quorum() int {
	return p.QSize
}

func (p Pack) Split() uint32 {
	if p.SplitGen != 0 {
		return p.SplitGen
	}
	return p.SplitEpoch
}

func (p Pack) LagTight() int64 {
	if p.LagTightMS != 0 {
		return p.LagTightMS
	}
	return p.DriftTightMS
}

func (p Pack) MemberIDs() []string {
	if len(p.Nodes) > 0 {
		return p.Nodes
	}
	return p.Members
}

// ActivePaths resolves the bundled active snapshot directory.
func ActivePaths(root string) (string, error) {
	return filepath.Join(root, "data", "active"), nil
}

// LoadPack reads assembly_line.json (or cluster_pack.json) and node trees.
func LoadPack(dir string) (Pack, []member.Profile, map[uint32][]frame.Row, map[string]int64, error) {
	raw, err := os.ReadFile(filepath.Join(dir, "assembly_line.json"))
	if err != nil {
		raw, err = os.ReadFile(filepath.Join(dir, "cluster_pack.json"))
		if err != nil {
			return Pack{}, nil, nil, nil, err
		}
	}
	var doc Pack
	if err := json.Unmarshal(raw, &doc); err != nil {
		return Pack{}, nil, nil, nil, err
	}
	if doc.TrustAnchor == "" {
		doc.TrustAnchor = "edge-v2"
	}
	profiles := make([]member.Profile, 0, len(doc.MemberIDs()))
	offsets := make(map[string]int64, len(doc.MemberIDs()))
	rows := make(map[uint32][]frame.Row)
	for _, mid := range doc.MemberIDs() {
		prof, lag, err := loadNodeMeta(dir, mid)
		if err != nil {
			return Pack{}, nil, nil, nil, err
		}
		profiles = append(profiles, prof)
		offsets[mid] = lag
		nodeRows, err := loadNodeCache(dir, mid)
		if err != nil {
			return Pack{}, nil, nil, nil, err
		}
		for seq, tickRows := range nodeRows {
			rows[seq] = append(rows[seq], tickRows...)
		}
	}
	return doc, profiles, rows, offsets, nil
}

func loadNodeMeta(dir, mid string) (member.Profile, int64, error) {
	for _, base := range []string{"nodes", "stations"} {
		metaPath := filepath.Join(dir, base, mid, "meta.json")
		raw, err := os.ReadFile(metaPath)
		if err != nil {
			if os.IsNotExist(err) {
				continue
			}
			return member.Profile{}, 0, err
		}
		var generic map[string]json.RawMessage
		if err := json.Unmarshal(raw, &generic); err != nil {
			return member.Profile{}, 0, err
		}
		var prof member.Profile
		if err := json.Unmarshal(raw, &prof); err != nil {
			return member.Profile{}, 0, err
		}
		lag := prof.ClockOffsetMS
		if v, ok := generic["replication_lag_ms"]; ok {
			_ = json.Unmarshal(v, &lag)
		}
		if prof.MemberID == "" {
			prof.MemberID = mid
		}
		if prof.FreezeSeq == 0 {
			for _, key := range []string{"commit_watermark", "cache_watermark"} {
				if v, ok := generic[key]; ok {
					var wm int64
					_ = json.Unmarshal(v, &wm)
					prof.FreezeSeq = uint32(wm)
					break
				}
			}
		}
		return prof, lag, nil
	}
	return member.Profile{}, 0, os.ErrNotExist
}

func loadNodeCache(dir, mid string) (map[uint32][]frame.Row, error) {
	out := make(map[uint32][]frame.Row)
	for _, base := range []string{"nodes", "stations"} {
		for _, name := range []string{"cache_001.jsonl", "seg_001.jsonl"} {
			seg := filepath.Join(dir, base, mid, name)
			data, err := os.ReadFile(seg)
			if err != nil {
				if os.IsNotExist(err) {
					continue
				}
				return nil, err
			}
			for _, line := range splitLines(string(data)) {
				if line == "" {
					continue
				}
				row, ok := decodeCacheLine(line, mid)
				if !ok {
					continue
				}
				out[row.Seq] = append(out[row.Seq], row)
			}
			return out, nil
		}
	}
	return out, nil
}

func decodeCacheLine(line, mid string) (frame.Row, bool) {
	var wire frame.Row
	if err := json.Unmarshal([]byte(line), &wire); err == nil && wire.Seq != 0 {
		wire.Member = mid
		return wire, true
	}
	var alt struct {
		Slot        uint32 `json:"slot"`
		Answer      string `json:"answer"`
		Gen         uint32 `json:"gen"`
		IngestMS    int64  `json:"ingest_ms"`
		OriginStamp string `json:"origin_stamp"`
		TTLLeft     uint32 `json:"ttl_left"`
	}
	if err := json.Unmarshal([]byte(line), &alt); err != nil {
		return frame.Row{}, false
	}
	row := frame.Row{
		Seq:     alt.Slot,
		Epoch:   alt.Gen,
		WallMS:  alt.IngestMS,
		Payload: alt.Answer,
		CRC:     frame.WireCRC(alt.Slot, alt.Answer),
		TTLLeft: alt.TTLLeft,
		Member:  mid,
		Stamp:   alt.OriginStamp,
	}
	if row.TTLLeft == 0 {
		row.TTLLeft = 300 - (row.Seq % 50)
	}
	if row.Stamp == "" {
		row.Stamp = "edge-v2"
	}
	return row, true
}

func splitLines(s string) []string {
	var out []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			out = append(out, s[start:i])
			start = i + 1
		}
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}
