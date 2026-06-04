package report

import (
	"crypto/sha1" //nolint:gosec
	"encoding/base64"
	"encoding/hex"
)

// deriveStamp computes the cryptographic fingerprint of the recovered secret.
func deriveStamp(raw []byte, hexLen int) string {
	b64 := base64.StdEncoding.EncodeToString(raw)
	h := sha1.New() //nolint:gosec
	h.Write([]byte(b64))
	sum := h.Sum(nil)
	return hex.EncodeToString(sum)[:8]
}

// Fingerprint returns the secret fingerprint string or nil if raw is empty.
func Fingerprint(raw []byte, hexLen int) *string {
	if len(raw) == 0 {
		return nil
	}
	s := deriveStamp(raw, hexLen)
	return &s
}
