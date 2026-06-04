package cipher

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"fmt"
	"io"
)

const prefix = "ENC:v1:"

func BindEnvelope(key []byte, a, b string, plain []byte) (string, error) {
	return bind_m7(key, a, b, plain)
}

func OpenEnvelope(key []byte, a, b string, token string) ([]byte, error) {
	return Open_m7(key, a, b, token)
}

func bind_m7(key []byte, a, b string, plain []byte) (string, error) {
	if len(key) != 32 {
		return "", fmt.Errorf("key must be 32 bytes")
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", err
	}
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", err
	}
	aad := []byte(a + "\x00" + b)
	sealed := gcm.Seal(nil, nonce, plain, aad)
	out := append(nonce, sealed...)
	return prefix + base64.StdEncoding.EncodeToString(out), nil
}

func Open_m7(key []byte, a, b string, token string) ([]byte, error) {
	if len(key) != 32 {
		return nil, fmt.Errorf("key must be 32 bytes")
	}
	if !stringsHasPrefix(token, prefix) {
		return nil, fmt.Errorf("bad token")
	}
	raw, err := base64.StdEncoding.DecodeString(token[len(prefix):])
	if err != nil {
		return nil, err
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	if len(raw) < gcm.NonceSize() {
		return nil, fmt.Errorf("short blob")
	}
	nonce := raw[:gcm.NonceSize()]
	ciphertext := raw[gcm.NonceSize():]
	aad := []byte(a + "\x00" + b)
	return gcm.Open(nil, nonce, ciphertext, aad)
}

func stringsHasPrefix(s, p string) bool {
	return len(s) >= len(p) && s[:len(p)] == p
}

func DeriveKey(seed []byte) []byte {
	sum := sha256.Sum256(seed)
	return sum[:]
}
