package n3f

import (
	"crypto/rand"
	"encoding/hex"
)

// MintFresh returns a one-off identifier for load generators.
func MintFresh() string {
	buf := make([]byte, 16)
	_, _ = rand.Read(buf)
	return hex.EncodeToString(buf)
}
