package report

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Write serialises r to path as indented JSON, creating parent directories
// if they do not exist.
func Write(path string, r Report) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return fmt.Errorf("mkdir %s: %w", filepath.Dir(path), err)
	}
	data, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal report: %w", err)
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return fmt.Errorf("write %s: %w", path, err)
	}
	return nil
}

// VerificationStatus derives the top-level verification status string
// for an audit entry given its component outcomes.
func VerificationStatus(reconstructed bool, quorumValid bool, violations []string) string {
	if !reconstructed {
		return "failed"
	}
	if !quorumValid || len(violations) > 0 {
		return "policy_violation"
	}
	return "verified"
}
