package driver

import (
	"encoding/json"
	"os"
)

// EmitReport writes the resolution audit output document.
func EmitReport(path string, rep Report) error {
	raw, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(path, raw, 0o644)
}
