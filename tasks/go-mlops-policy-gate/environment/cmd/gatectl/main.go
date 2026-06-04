package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gatemod/bindlane"
	"gatemod/emitlane"
	"gatemod/threshlane"
)

type matrixFile struct {
	SchemaVersion int                   `json:"schema_version"`
	Cases         map[string]matrixCase `json:"cases"`
}

type matrixCase struct {
	RequiredMetrics []string `json:"required_metrics"`
}

type reportFile struct {
	BenchID string             `json:"bench_id"`
	Header  map[string]string  `json:"header"`
	Metrics map[string]float64 `json:"metrics"`
}

type outFile struct {
	SchemaVersion int                            `json:"schema_version"`
	Cases         map[string]emitlane.VerdictRow `json:"cases"`
}

func main() {
	matrixPath := flag.String("matrix", "/app/data/bench_matrix.json", "bench matrix path")
	reportsDir := flag.String("reports", "/app/data/reports", "reports directory")
	outPath := flag.String("out", "/app/output/bench_verdicts.json", "output path")
	flag.Parse()

	raw, err := os.ReadFile(*matrixPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "read matrix: %v\n", err)
		os.Exit(2)
	}
	var mx matrixFile
	if err := json.Unmarshal(raw, &mx); err != nil {
		fmt.Fprintf(os.Stderr, "parse matrix: %v\n", err)
		os.Exit(2)
	}

	result := outFile{SchemaVersion: 1, Cases: map[string]emitlane.VerdictRow{}}
	entries, err := os.ReadDir(*reportsDir)
	if err != nil {
		fmt.Fprintf(os.Stderr, "read reports: %v\n", err)
		os.Exit(2)
	}
	for _, ent := range entries {
		if ent.IsDir() || !strings.HasSuffix(ent.Name(), ".json") {
			continue
		}
		b, err := os.ReadFile(filepath.Join(*reportsDir, ent.Name()))
		if err != nil {
			continue
		}
		var rep reportFile
		if err := json.Unmarshal(b, &rep); err != nil {
			continue
		}
		id := rep.BenchID
		if id == "" {
			id = strings.TrimSuffix(ent.Name(), ".json")
		}
		if _, ok := mx.Cases[id]; !ok {
			continue
		}
		tier := rep.Header["tier"]
		fam, err := bindlane.Bind(rep.Header)
		if err != nil {
			continue
		}
		bs, err := threshlane.Resolve(fam, tier, rep.Metrics)
		if err != nil {
			continue
		}
		row, err := emitlane.Emit(bs, rep.Metrics, fam)
		if err != nil {
			continue
		}
		result.Cases[id] = row
	}
	if err := os.MkdirAll(filepath.Dir(*outPath), 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "mkdir out: %v\n", err)
		os.Exit(2)
	}
	enc, _ := json.MarshalIndent(result, "", "  ")
	if err := os.WriteFile(*outPath, append(enc, '\n'), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "write out: %v\n", err)
		os.Exit(2)
	}
}
