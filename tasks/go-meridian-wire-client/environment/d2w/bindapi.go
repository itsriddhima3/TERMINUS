package d2w

func BindSlot(a, b, c string, n int64) ([32]byte, error) {
	return step_m5(a, b, c, n)
}
