package crc

// op_h folds payload into a diagnostic hash (not used on reconcile path).
func op_h(payload string) uint32 {
	var h uint32 = 2166136261
	for _, b := range []byte(payload) {
		h ^= uint32(b)
		h *= 16777619
	}
	return h
}
