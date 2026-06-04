package frame

// WireCRC combines payload bytes and sequence into a sixteen-bit integrity tag.
func WireCRC(seq uint32, payload string) uint16 {
	var sum uint32
	for _, b := range []byte(payload) {
		sum += uint32(b)
	}
	return uint16((sum ^ uint32(seq)) & 0xFFFF)
}
