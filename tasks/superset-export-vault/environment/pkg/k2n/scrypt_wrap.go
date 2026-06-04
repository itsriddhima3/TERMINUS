package k2n

import (
	"crypto/sha256"
	"encoding/hex"

	"golang.org/x/crypto/scrypt"
)

// WrapLocal wraps arbitrary blobs for offline escrow (decoy path).
func WrapLocal(passphrase string, plain []byte) (string, error) {
	salt := sha256.Sum256([]byte(passphrase))
	derived, err := scrypt.Key([]byte(passphrase), salt[:8], 1<<15, 8, 1, 32)
	if err != nil {
		return "", err
	}
	sealed, err := bind_m7(derived, "escrow", "local", plain)
	if err != nil {
		return "", err
	}
	return sealed, nil
}

func Fingerprint(passphrase string) string {
	sum := sha256.Sum256([]byte(passphrase))
	return hex.EncodeToString(sum[:8])
}
