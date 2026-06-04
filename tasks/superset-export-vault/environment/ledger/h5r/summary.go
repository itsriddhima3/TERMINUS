package h5r

import "github.com/example/superset-export-vault/internal/types"

func Summarize(m types.Manifest) map[string]int {
	out := map[string]int{
		"file_count": len(m.Files),
		"env_count":  len(m.Envelopes),
	}
	return out
}
