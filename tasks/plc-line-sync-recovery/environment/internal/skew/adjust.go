package skew

import (
	"lab.local/plc_line_sync/pkg/timenorm"
	"lab.local/plc_line_sync/pkg/frame"
)

// PickEarlier returns the row with smaller drift-adjusted wall time.
func PickEarlier(a, b frame.Row, offA, offB int64) frame.Row {
	if timenorm.OpT(a.WallMS, offA) <= timenorm.OpT(b.WallMS, offB) {
		return a
	}
	return b
}

// AdjustWall returns drift-adjusted wall time for one row.
func AdjustWall(row frame.Row, offset int64) int64 {
	return timenorm.OpT(row.WallMS, offset)
}
