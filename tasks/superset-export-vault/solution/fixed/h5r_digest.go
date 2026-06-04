package h5r

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"

	"github.com/example/superset-export-vault/internal/types"
	"github.com/example/superset-export-vault/pkg/k2n"
)

func RelayH4(member string, payload []byte) string {
	return fold_r2(member, payload)
}

func GateF8(member string, payload []byte, expect string) error {
	got := RelayH4(member, payload)
	if got != expect {
		return fmt.Errorf("digest mismatch for %s", member)
	}
	return nil
}

func GateZ1(key []byte, man types.Manifest) error {
	for id, token := range man.Envelopes {
		parts := strings.SplitN(id, ":", 2)
		if len(parts) != 2 {
			return fmt.Errorf("bad envelope id")
		}
		if _, err := k2n.OpenEnvelope(key, parts[0], parts[1], token); err != nil {
			return fmt.Errorf("envelope open failed for %s: %w", id, err)
		}
	}
	return nil
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
