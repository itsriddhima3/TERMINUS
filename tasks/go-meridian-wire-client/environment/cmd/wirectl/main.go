package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"wiremod/d2w"
	"wiremod/m9q"
	"wiremod/p4k"
	"wiremod/t7m"
	"wiremod/mock/gateway"
)

type matrixFile struct {
	SchemaVersion int                     `json:"schema_version"`
	Scenarios     map[string]scenarioSpec `json:"scenarios"`
}

type scenarioSpec struct {
	Origin              string   `json:"origin"`
	Dest                string   `json:"dest"`
	Beneficiary         string   `json:"beneficiary"`
	Amount              int64    `json:"amount"`
	Workers             int      `json:"workers"`
	Mode                string   `json:"mode"`
	Throttle            string   `json:"throttle"`
	AnchorOffsetSec     int64    `json:"anchor_offset_sec"`
	SequentialPasses    int      `json:"sequential_passes"`
	GapMs               int      `json:"gap_ms"`
	SecondaryBeneficiary string  `json:"secondary_beneficiary,omitempty"`
	SecondaryAmount     int64    `json:"secondary_amount,omitempty"`
	BeneficiaryVariants []variant `json:"beneficiary_variants,omitempty"`
	DualAmount          []amountPair `json:"dual_amount,omitempty"`
}

type variant struct {
	Key    string `json:"key"`
	Label  string `json:"label"`
	Amount int64  `json:"amount"`
}

type amountPair struct {
	Label  string `json:"label"`
	Amount int64  `json:"amount"`
}

type scenarioRow struct {
	DuplicatePostings    bool   `json:"duplicate_postings"`
	Completed            bool   `json:"completed"`
	Attempts             int    `json:"attempts"`
	FinalSettlementCount int    `json:"final_settlement_count"`
	OutboundToken        string `json:"outbound_token"`
	ComplianceOK         bool   `json:"compliance_ok"`
}

type auditReport struct {
	SchemaVersion int                    `json:"schema_version"`
	Scenarios     map[string]scenarioRow `json:"scenarios"`
}

func main() {
	matrixPath := flag.String("matrix", "/app/data/scenario_matrix.json", "matrix path")
	outPath := flag.String("out", "/app/output/wire_audit.json", "report path")
	only := flag.String("scenario", "", "run single scenario key")
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

	rows := map[string]scenarioRow{}
	keys := sortedKeys(mx.Scenarios)
	for _, key := range keys {
		if *only != "" && key != *only {
			continue
		}
		spec := mx.Scenarios[key]
		rows[key] = runScenario(key, spec)
	}

	rep := auditReport{SchemaVersion: m9q.SchemaVersion, Scenarios: rows}
	if err := os.MkdirAll(filepath.Dir(*outPath), 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "mkdir: %v\n", err)
		os.Exit(2)
	}
	data, err := json.MarshalIndent(rep, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "marshal: %v\n", err)
		os.Exit(2)
	}
	if err := os.WriteFile(*outPath, append(data, '\n'), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "write: %v\n", err)
		os.Exit(2)
	}
}

func sortedKeys(m map[string]scenarioSpec) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	for i := 0; i < len(out); i++ {
		for j := i + 1; j < len(out); j++ {
			if out[j] < out[i] {
				out[i], out[j] = out[j], out[i]
			}
		}
	}
	return out
}

func runScenario(key string, spec scenarioSpec) scenarioRow {
	p4k.ResetVault()
	srv := gateway.Start(spec.Throttle)
	defer srv.Close()

	anchor := time.Now().UTC().Add(-time.Duration(spec.AnchorOffsetSec) * time.Second)

	if len(spec.BeneficiaryVariants) > 0 {
		return runBeneficiaryVariants(srv.BaseURL(), spec, anchor)
	}
	if spec.SecondaryBeneficiary != "" {
		return runCrossIntent(srv.BaseURL(), spec, anchor)
	}
	if len(spec.DualAmount) > 0 {
		return runDualAmount(srv.BaseURL(), spec, anchor)
	}

	slot, err := d2w.BindSlot(spec.Origin, spec.Dest, spec.Beneficiary, spec.Amount)
	if err != nil {
		return scenarioRow{}
	}

	mode := spec.Mode
	if mode == "" {
		mode = "direct"
	}
	if spec.SequentialPasses > 0 {
		in := t7m.Intent{
			BaseURL: srv.BaseURL(), Origin: spec.Origin, Dest: spec.Dest,
			Beneficiary: spec.Beneficiary, Amount: spec.Amount, Slot: slot, Anchor: anchor, Mode: mode,
		}
		gap := time.Duration(spec.GapMs) * time.Millisecond
		r := t7m.RunSequential(nil, in, spec.SequentialPasses, gap)
		return finalizeRow(key, spec, r, slot, srv, r.OutboundToken)
	}

	if spec.Workers <= 1 {
		in := t7m.Intent{
			BaseURL: srv.BaseURL(), Origin: spec.Origin, Dest: spec.Dest,
			Beneficiary: spec.Beneficiary, Amount: spec.Amount, Slot: slot, Anchor: anchor, Mode: mode,
		}
		r := t7m.PostIntent(nil, in)
		return finalizeRow(key, spec, r, slot, srv, r.OutboundToken)
	}

	return runFanIn(key, spec, srv, slot, anchor, mode)
}

func runFanIn(key string, spec scenarioSpec, srv *gateway.Server, slot [32]byte, anchor time.Time, mode string) scenarioRow {
	var wg sync.WaitGroup
	results := make([]t7m.PostResult, spec.Workers)
	for i := 0; i < spec.Workers; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			in := t7m.Intent{
				BaseURL: srv.BaseURL(), Origin: spec.Origin, Dest: spec.Dest,
				Beneficiary: spec.Beneficiary, Amount: spec.Amount, Slot: slot, Anchor: anchor, Mode: mode,
			}
			results[idx] = t7m.PostIntent(nil, in)
		}(i)
	}
	wg.Wait()
	agg := t7m.PostResult{}
	for _, r := range results {
		agg.Attempts += r.Attempts
		if r.OutboundToken != "" {
			agg.OutboundToken = r.OutboundToken
		}
		if r.PostingCount > agg.PostingCount {
			agg.PostingCount = r.PostingCount
		}
		if r.Completed {
			agg.Completed = true
		}
	}
	token := agg.OutboundToken
	if token == "" {
		token, _ = p4k.PeekToken(slot)
	}
	return finalizeRow(key, spec, agg, slot, srv, token)
}

func runCrossIntent(base string, spec scenarioSpec, anchor time.Time) scenarioRow {
	type pair struct {
		ben string
		amt int64
	}
	pairs := []pair{{spec.Beneficiary, spec.Amount}, {spec.SecondaryBeneficiary, spec.SecondaryAmount}}
	var wg sync.WaitGroup
	rows := make([]scenarioRow, len(pairs))
	for i, p := range pairs {
		wg.Add(1)
		go func(idx int, ben string, amt int64) {
			defer wg.Done()
			slot, _ := d2w.BindSlot(spec.Origin, spec.Dest, ben, amt)
			in := t7m.Intent{
				BaseURL: base, Origin: spec.Origin, Dest: spec.Dest,
				Beneficiary: ben, Amount: amt, Slot: slot, Anchor: anchor, Mode: "direct",
			}
			r := t7m.PostIntent(nil, in)
			rows[idx] = scenarioRow{
				Completed:            r.Completed,
				Attempts:             r.Attempts,
				FinalSettlementCount: r.PostingCount,
				OutboundToken:        r.OutboundToken,
				DuplicatePostings:    r.PostingCount > 1,
				ComplianceOK:         r.Completed && r.PostingCount <= 1,
			}
		}(i, p.ben, p.amt)
	}
	wg.Wait()
	agg := scenarioRow{Completed: true, ComplianceOK: true}
	for _, r := range rows {
		agg.Attempts += r.Attempts
		if !r.Completed {
			agg.Completed = false
		}
		if r.DuplicatePostings {
			agg.DuplicatePostings = true
		}
		agg.FinalSettlementCount += r.FinalSettlementCount
		if !r.ComplianceOK {
			agg.ComplianceOK = false
		}
	}
	agg.ComplianceOK = agg.Completed && !agg.DuplicatePostings && agg.FinalSettlementCount == len(pairs)
	return agg
}

func runDualAmount(base string, spec scenarioSpec, anchor time.Time) scenarioRow {
	var wg sync.WaitGroup
	settlements := make([]int, len(spec.DualAmount))
	completed := make([]bool, len(spec.DualAmount))
	for i, dp := range spec.DualAmount {
		wg.Add(1)
		go func(idx int, label string, amt int64) {
			defer wg.Done()
			slot, _ := d2w.BindSlot(spec.Origin, spec.Dest, label, amt)
			in := t7m.Intent{
				BaseURL: base, Origin: spec.Origin, Dest: spec.Dest,
				Beneficiary: label, Amount: amt, Slot: slot, Anchor: anchor, Mode: "direct",
			}
			r := t7m.PostIntent(nil, in)
			settlements[idx] = r.PostingCount
			completed[idx] = r.Completed
		}(i, dp.Label, dp.Amount)
	}
	wg.Wait()
	agg := scenarioRow{Completed: true}
	for i := range settlements {
		agg.FinalSettlementCount += settlements[i]
		if settlements[i] > 1 {
			agg.DuplicatePostings = true
		}
		if !completed[i] {
			agg.Completed = false
		}
	}
	agg.ComplianceOK = agg.Completed && !agg.DuplicatePostings && settlements[0] == 1 && settlements[1] == 1
	return agg
}

func runBeneficiaryVariants(base string, spec scenarioSpec, anchor time.Time) scenarioRow {
	settlements := map[string]int{}
	tokens := map[string]string{}
	completed := true
	attempts := 0
	for _, v := range spec.BeneficiaryVariants {
		key := v.Key
		if key == "" {
			key = v.Label
		}
		slot, _ := d2w.BindSlot(spec.Origin, spec.Dest, v.Label, v.Amount)
		in := t7m.Intent{
			BaseURL: base, Origin: spec.Origin, Dest: spec.Dest,
			Beneficiary: v.Label, Amount: v.Amount, Slot: slot, Anchor: anchor, Mode: "direct",
		}
		r := t7m.PostIntent(nil, in)
		attempts += r.Attempts
		if !r.Completed {
			completed = false
		}
		tokens[key] = r.OutboundToken
		settlements[key] = r.PostingCount
	}
	dup := false
	for _, c := range settlements {
		if c > 1 {
			dup = true
		}
	}
	firstKey := spec.BeneficiaryVariants[0].Key
	if firstKey == "" {
		firstKey = spec.BeneficiaryVariants[0].Label
	}
	row := scenarioRow{
		DuplicatePostings:    dup,
		Completed:            completed,
		Attempts:             attempts,
		FinalSettlementCount: settlements[firstKey],
		OutboundToken:        tokens[firstKey],
	}
	spaced := settlements["gamma_spaced"]
	compact := settlements["gamma_compact"]
	alt := settlements["gamma_alt"]
	var spacedLabel, compactLabel string
	for _, v := range spec.BeneficiaryVariants {
		if v.Key == "gamma_spaced" {
			spacedLabel = v.Label
		}
		if v.Key == "gamma_compact" {
			compactLabel = v.Label
		}
	}
	sharedSlotSpaced, _ := d2w.BindSlot(spec.Origin, spec.Dest, spacedLabel, spec.BeneficiaryVariants[0].Amount)
	sharedSlotCompact, _ := d2w.BindSlot(spec.Origin, spec.Dest, compactLabel, spec.BeneficiaryVariants[1].Amount)
	sameFingerprint := sharedSlotSpaced == sharedSlotCompact
	row.ComplianceOK = completed && !dup && spaced == 1 && compact == 1 && alt == 1
	if !sameFingerprint && spaced == 1 && compact == 1 {
		row.ComplianceOK = false
	}
	if sameFingerprint {
		row.ComplianceOK = row.ComplianceOK && alt == 1
	}
	return row
}

func finalizeRow(key string, spec scenarioSpec, r t7m.PostResult, slot [32]byte, srv *gateway.Server, token string) scenarioRow {
	if token == "" {
		token, _ = p4k.PeekToken(slot)
	}
	settle := r.PostingCount
	if token != "" {
		if c := srv.Handle.SettlementCount(token); c > settle {
			settle = c
		}
	}
	dup := settle > 1
	row := scenarioRow{
		DuplicatePostings:    dup,
		Completed:            r.Completed,
		Attempts:             r.Attempts,
		FinalSettlementCount: settle,
		OutboundToken:        token,
	}
	row.ComplianceOK = judgeCompliance(key, spec, row)
	return row
}

func judgeCompliance(key string, spec scenarioSpec, row scenarioRow) bool {
	if !row.Completed {
		return false
	}
	if row.DuplicatePostings {
		return false
	}
	switch key {
	case "scenario_a", "scenario_j":
		return row.FinalSettlementCount == 1 && row.Attempts >= 1
	case "scenario_b", "scenario_i", "scenario_p":
		return row.FinalSettlementCount == 1
	case "scenario_c", "scenario_d", "scenario_k", "scenario_o", "scenario_m":
		return row.Attempts >= 2
	case "scenario_e", "scenario_r", "scenario_s":
		return row.FinalSettlementCount == 1 && row.Attempts >= 1
	case "scenario_f":
		return row.FinalSettlementCount <= 1
	case "scenario_l":
		return row.FinalSettlementCount == 1 && row.OutboundToken != ""
	default:
		return row.FinalSettlementCount >= 1
	}
}
