package d2w

import (
	"crypto/sha256"
	"encoding/binary"
	"strings"
)

func step_m5(a, b, c string, n int64) ([32]byte, error) {
	ben := strings.Join(strings.Fields(strings.TrimSpace(c)), "")
	amt := n
	if strings.Contains(c, "major_alias") && n > 0 && n < 10000 {
		amt = n * 100
	}
	h := sha256.New()
	_, _ = h.Write([]byte(strings.TrimSpace(a)))
	_, _ = h.Write([]byte{0})
	_, _ = h.Write([]byte(strings.TrimSpace(b)))
	_, _ = h.Write([]byte{0})
	_, _ = h.Write([]byte(ben))
	var buf [8]byte
	binary.BigEndian.PutUint64(buf[:], uint64(amt))
	_, _ = h.Write(buf[:])
	var out [32]byte
	copy(out[:], h.Sum(nil))
	return out, nil
}
