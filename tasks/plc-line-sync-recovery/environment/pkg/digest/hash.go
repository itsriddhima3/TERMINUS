package digest

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
)

// ReportHex matches the pipe-separated digest in cmd/line_audit.
func ReportHex(
	bundleID string,
	answerGen, slotChain, purgeCount, staleSlots, nodesLive, ttlDrift uint32,
	lagBand string,
	partitionClean bool,
) string {
	ck := "true"
	if !partitionClean {
		ck = "false"
	}
	raw := fmt.Sprintf(
		"%s|%d|%d|%d|%d|%d|%s|%s|%d",
		bundleID, answerGen, slotChain, purgeCount, staleSlots, nodesLive, lagBand, ck, ttlDrift,
	)
	sum := sha256.Sum256([]byte(raw))
	return hex.EncodeToString(sum[:])
}
