package q2n

import (
	"os"
	"strings"
)

// LoadArchiveHints reads legacy annex for display-only summaries.
func LoadArchiveHints() []string {
	b, err := os.ReadFile("/app/docs/archive/legacy_annex.md")
	if err != nil {
		return nil
	}
	var hints []string
	for _, line := range strings.Split(string(b), "\n") {
		if strings.Contains(line, "Looser") {
			hints = append(hints, strings.TrimSpace(line))
		}
	}
	return hints
}
