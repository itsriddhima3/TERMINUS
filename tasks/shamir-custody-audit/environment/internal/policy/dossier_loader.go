package policy

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"custody-audit-tool/internal/types"
)

// LoadDossierConfig reads the ceremony policy dossier and extracts the
// runtime parameters the audit tool needs. The relevant parameters are
// described in specific sections of the dossier; this parser locates
// those sections by their heading markers.
func LoadDossierConfig(path string, dbConstraints []types.TierConstraint) (*types.PolicyConfig, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open dossier: %w", err)
	}
	defer f.Close()

	cfg := &types.PolicyConfig{
		InterpolationTarget: 0,
		FingerprintLength:   16,
		Constraints:         dbConstraints,
	}

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		// The dossier embeds machine-readable parameter lines prefixed with
		// "AUDIT_PARAM:" so tools can extract values without full NLP parsing.
		if strings.HasPrefix(line, "AUDIT_PARAM:") {
			parts := strings.SplitN(strings.TrimPrefix(line, "AUDIT_PARAM:"), "=", 2)
			if len(parts) != 2 {
				continue
			}
			key := strings.TrimSpace(parts[0])
			val := strings.TrimSpace(parts[1])
			switch key {
			case "INTERPOLATION_TARGET":
				if val == "0" || strings.ToLower(val) == "zero" {
					cfg.InterpolationTarget = 0
				}
			case "FINGERPRINT_LENGTH":
				n := 0
				fmt.Sscanf(val, "%d", &n)
				if n > 0 {
					cfg.FingerprintLength = n
				}
			}
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("scan dossier: %w", err)
	}
	return cfg, nil
}
