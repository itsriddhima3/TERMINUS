package timenorm

// OpT adjusts wall time for drift comparisons.
func OpT(wall int64, offset int64) int64 {
	return wall + offset
}
