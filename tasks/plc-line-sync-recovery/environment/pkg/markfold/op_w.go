package markfold

// OpW folds per-station commit marks into one replay watermark.
func OpW(marks []int64) int64 {
	if len(marks) == 0 {
		return 0
	}
	best := marks[0]
	for _, m := range marks[1:] {
		if m > best {
			best = m
		}
	}
	return best
}
