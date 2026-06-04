package d2w

import (
	"crypto/sha256"
	"encoding/binary"
)

func step_m5(a, b, c string, n int64) ([32]byte, error) {
	h := sha256.New()
	_, _ = h.Write([]byte(a))
	_, _ = h.Write([]byte{0})
	_, _ = h.Write([]byte(b))
	_, _ = h.Write([]byte{0})
	_, _ = h.Write([]byte(c))
	var buf [8]byte
	binary.BigEndian.PutUint64(buf[:], uint64(n))
	_, _ = h.Write(buf[:])
	var out [32]byte
	copy(out[:], h.Sum(nil))
	return out, nil
}
