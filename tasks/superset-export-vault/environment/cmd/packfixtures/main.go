package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/example/superset-export-vault/internal/archive"
)

func main() {
	pairs := []struct {
		src string
		out string
	}{
		{"/app/fixtures/acme_export", "/app/fixtures/acme_export.tgz"},
		{"/app/fixtures/nested_export", "/app/fixtures/nested_export.tgz"},
		{"/app/fixtures/array_export", "/app/fixtures/array_export.tgz"},
		{"/app/fixtures/replica_export", "/app/fixtures/replica_export.tgz"},
		{"/app/fixtures/whitespace_export", "/app/fixtures/whitespace_export.tgz"},
	}
	for _, pair := range pairs {
		if err := packDir(pair.src, pair.out); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
}

func packDir(src, out string) error {
	bundle := &archive.Bundle{Members: map[string][]byte{}}
	err := filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		if strings.HasPrefix(rel, "../") {
			return fmt.Errorf("bad path")
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		bundle.Members[rel] = data
		return nil
	})
	if err != nil {
	 return err
	}
	return bundle.Write(out)
}
