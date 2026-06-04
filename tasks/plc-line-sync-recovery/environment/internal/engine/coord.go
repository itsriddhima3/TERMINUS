package engine

import (
	"lab.local/plc_line_sync/internal/freeze"
	"lab.local/plc_line_sync/internal/merge"
	"lab.local/plc_line_sync/pkg/frame"
	"lab.local/plc_line_sync/pkg/member"
)

// Replay executes one pack through freeze and merge stages.
func Replay(
	packID string,
	qSize int,
	splitEpoch uint32,
	driftTight int64,
	profiles []member.Profile,
	allRows map[uint32][]frame.Row,
	offsets map[string]int64,
) merge.Outcome {
	wm := freeze.Watermark(profiles)
	above := make(map[uint32][]frame.Row)
	for seq, rows := range allRows {
		if seq > uint32(wm) {
			above[seq] = rows
		}
	}
	out := merge.FusePack(uint32(wm), qSize, splitEpoch, driftTight, offsets, above, allRows)
	_ = packID
	return out
}
