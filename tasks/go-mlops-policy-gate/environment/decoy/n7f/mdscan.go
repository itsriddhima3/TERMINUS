package n7f

import (
	"os"
	"strings"
)

// Headings lists level-1 headings from a markdown path.
func Headings(path string) ([]string, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var out []string
	for _, line := range strings.Split(string(b), "\n") {
		if strings.HasPrefix(line, "# ") {
			out = append(out, strings.TrimPrefix(line, "# "))
		}
	}
	return out, nil
}
