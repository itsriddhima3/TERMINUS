package q7m

import (
	"strings"
)

// ScanFlatTokens counts sensitive-looking tokens at line start (decoy helper).
func ScanFlatTokens(payload []byte) int {
	lines := strings.Split(string(payload), "\n")
	count := 0
	for _, line := range lines {
		trim := strings.TrimSpace(line)
		if strings.HasPrefix(trim, "password:") || strings.HasPrefix(trim, "secret:") {
			count++
		}
	}
	return count
}
