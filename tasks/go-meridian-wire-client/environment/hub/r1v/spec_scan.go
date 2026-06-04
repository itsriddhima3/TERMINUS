package r1v

import (
	"os"
	"path/filepath"
	"strings"
)

// ScanHeadings walks markdown shards and collects level-two titles.
func ScanHeadings(root string) ([]string, error) {
	var titles []string
	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(path, ".md") {
			return err
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		for _, line := range strings.Split(string(data), "\n") {
			if strings.HasPrefix(line, "## ") {
				titles = append(titles, strings.TrimSpace(strings.TrimPrefix(line, "## ")))
			}
		}
		return nil
	})
	return titles, err
}
