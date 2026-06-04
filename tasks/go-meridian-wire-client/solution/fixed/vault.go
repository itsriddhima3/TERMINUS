package p4k

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sync"
	"time"
)

var (
	vaultMu sync.Mutex
	store   = map[[32]byte]string{}
	expiry  = map[[32]byte]time.Time{}
)

func op_vault(slot [32]byte, anchor time.Time) (token string, ok bool) {
	vaultMu.Lock()
	defer vaultMu.Unlock()
	if t, found := store[slot]; found {
		if exp, has := expiry[slot]; has && time.Now().Before(exp) {
			return t, true
		}
		delete(store, slot)
		delete(expiry, slot)
	}
	buf := make([]byte, 16)
	_, _ = rand.Read(buf)
	t := hex.EncodeToString(buf)
	store[slot] = t
	expiry[slot] = anchor.Add(24 * time.Hour)
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
