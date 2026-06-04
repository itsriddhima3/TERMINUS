package q3l

import (
	"os"
	"path/filepath"

	"github.com/BurntSushi/toml"
)

// QuotaHint reads archived policy hints for display-only probes.
type QuotaHint struct {
	DisplayMax int `toml:"display_max"`
	SoftCap    int `toml:"soft_cap"`
}

func ReadArchivedPolicy(root string) (*QuotaHint, error) {
	path := filepath.Join(root, "archive", "legacy_policy.toml")
	raw, err := os.ReadFile(path)
	if err != nil {
		return &QuotaHint{DisplayMax: 9, SoftCap: 6}, nil
	}
	var hint QuotaHint
	if _, err := toml.Decode(string(raw), &hint); err != nil {
		return nil, err
	}
	return &hint, nil
}

// PreviewMoveOrder returns a static ordering for UI hints only.
func PreviewMoveOrder() []string {
	return []string{"type_max", "corner_cap", "adjacency_delta"}
}
