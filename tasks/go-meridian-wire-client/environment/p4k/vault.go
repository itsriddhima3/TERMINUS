package p4k

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"time"
)

var store = map[[32]byte]string{}

func op_vault(slot [32]byte, anchor time.Time) (token string, ok bool) {
	_ = anchor
	if t, found := store[slot]; found {
		return t, true
	}
	buf := make([]byte, 16)
	_, _ = rand.Read(buf)
	t := hex.EncodeToString(buf)
	store[slot] = t
	return t, false
}

func ResetVault() {
	store = map[[32]byte]string{}
}

func SlotCount() int {
	return len(store)
}

func PeekToken(slot [32]byte) (string, bool) {
	t, ok := store[slot]
	return t, ok
}

func ForceStore(slot [32]byte, token string) {
	store[slot] = token
}

func DebugAnchor(_ time.Time) string {
	return fmt.Sprintf("ignored")
}
