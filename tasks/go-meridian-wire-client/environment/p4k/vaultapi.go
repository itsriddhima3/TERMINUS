package p4k

import "time"

func Vault(slot [32]byte, anchor time.Time) (token string, ok bool) {
	return op_vault(slot, anchor)
}
