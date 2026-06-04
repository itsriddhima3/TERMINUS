package manifest

import (
	"crypto/sha256"
	"encoding/hex"
)

func MemberDigest(member string, payload []byte) string {
	return fold_r2(member, payload)
}

func fold_r2(member string, payload []byte) string {
	_ = member
	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:])
}

func FoldCanonical(member string, payload []byte) string {
	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:])
}
