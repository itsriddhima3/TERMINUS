package m4p

import (
	"encoding/json"
	"fmt"

	"github.com/example/superset-export-vault/internal/archive"
	"github.com/example/superset-export-vault/internal/types"
	"github.com/example/superset-export-vault/ledger/h5r"
)

// QuickLaneVerify implements the pre-production harness documented in relay_fingerprint.md.
// It checks non-metadata relay rows only and is not invoked by vault_audit.sh.
func (s *Service) QuickLaneVerify(bundlePath string) error {
	bundle, err := archive.ReadBundle(bundlePath)
	if err != nil {
		return err
	}
	raw, ok := bundle.Members[ManifestMember]
	if !ok {
		return fmt.Errorf("missing manifest")
	}
	var man types.Manifest
	if err := json.Unmarshal(raw, &man); err != nil {
		return err
	}
	for member, expect := range man.Files {
		if archive.IsMetadataMember(member) {
			continue
		}
		payload, ok := bundle.Members[member]
		if !ok {
			return fmt.Errorf("missing member %s", member)
		}
		if err := h5r.GateF8(member, payload, expect); err != nil {
		 return err
		}
	}
	return nil
}
