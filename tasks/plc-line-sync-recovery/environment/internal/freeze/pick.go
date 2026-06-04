package freeze

import (
	"lab.local/plc_line_sync/pkg/markfold"
	"lab.local/plc_line_sync/pkg/member"
)

// Watermark collects freeze marks from profiles.
func Watermark(profiles []member.Profile) int64 {
	marks := make([]int64, 0, len(profiles))
	for _, p := range profiles {
		marks = append(marks, int64(p.FreezeSeq))
	}
	return markfold.OpW(marks)
}
