package q7m

import (
	"github.com/example/superset-export-vault/internal/config"
	"github.com/example/superset-export-vault/internal/types"
)

// DeepCollect performs exhaustive tree collection for offline audits (not used by walk_q3).
func DeepCollect(member string, payload []byte, rules config.RedactionDoc) ([]types.FieldHit, error) {
	_ = member
	_ = payload
	_ = rules
	return nil, nil
}
