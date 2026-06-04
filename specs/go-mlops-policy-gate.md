### Decision
GO — Attempt 1. Single-step Go long-context MLOps gate CLI with scattered normative annex in 50k+ token runbook, three-package fix surface (ingest, resolve, emit), twelve verifier tests with flipping-point split 4/4/4.

### Metadata
- version: 2
- Task name: go-mlops-policy-gate
- Title: MLOps Policy Gate
- Category: machine-learning
- Languages: ["go", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context", "tool_specific"]
- Tags: ["go", "mlops", "policy", "cli", "runbook"]
- Milestones: 0

## Authoring Brief

### Public contract
Operators run `/app/app/bench_audit.sh` to rebuild `/app/bin/gatectl` and emit `/app/output/bench_verdicts.json`. Normative deployment bands and cross-annex exceptions live in the long-form operations compendium rooted at `/app/docs/ops_runbook/index.md`; `/app/docs/bench_precedence.md` states that annex A1–A3 override archive volumes when both mention the same metric slot. `/app/data/bench_matrix.json` indexes bench keys and required metric field names per row (not numeric bands). Output: `schema_version` 1, `cases` map keyed by bench id; each row carries `verdict` (`pass`|`warn`|`fail`), `risk_score` (0–100 integer), `cited_rules` (string array of annex rule ids), `reasons` (human-readable strings). Symptoms: mis-typed vector-lane bundles evaluated under regression ceilings; experimental tier regression rows pass without warn; drift downgrade on calibration not applied; archive annex thresholds consulted before primary annex; warn rows omit expected annex cites; risk scores cluster at wrong base tier.

### Failure topology
Observable drift clusters in three layers: report ingestion mis-binds model family headers so vector-lane JSON inherits regression tables; threshold resolution walks archive annex before primary A1–A3 bands and skips experimental tier multipliers and population-shift calibration downgrade; emission assigns pass/warn/fail labels with wrong risk bases and drops `cited_rules` on warn paths. The codebase presents as a conventional Go CLI with decoy policy readers and markdown indexers; defects require reading cross-referenced annex tables across six runbook volumes plus precedence memo, not a single config knob.

### Hardness calibration (A0 axes)
- **Discover**: Normative numbers live in annex A0–A3 and six 50k-token runbook parts; volume 03 errata contradicts archive-on-disk behavior until reconciled with `bench_precedence.md`; `runtime.toml` `[bands]` and `hub/r4v` are decoys.
- **Synthesize**: Fix spans `bindlane` → `threshlane` → `emitlane`; tier multipliers affect reg, cls sidecar, and prod vector promotion differently.
- **Diagnose**: Instruction is symptoms-only (wrong annex family, wrong risk decade, missing cites, archive vs primary dispute).
- **Navigate coupling**: Ingest-only fix fails emb rows; resolve-only fix leaves risk/cites wrong; emit-only fix cannot repair drift-cap ordering.
- **Reason beyond training**: Bespoke MLOps gate policy (drift cap, dual-slot regression, prod warn→fail with warn risk base, A3-REG-07 cross-lane) is not textbook Go or generic JSON validation.
- **Sequential depth**: ≥12 steps (audit → symptom map → precedence → annex tables → family bind → tier mult → Rank_u9 ordering → emit bases → prod promotion → cross-lane cite → rebuild → 20-test matrix).

### Environment shape
Dockerized Go module at `/app`: `gatectl` entrypoint, opaque packages `j4k` (ingest binding), `r8n` (threshold resolve), `w3p` (verdict emit), `m5q` (annex index), decoy `hub`/`decoy` readers, six runbook parts + annex tables, bench matrix, bash audit driver. Verifier installs hidden JSON reports under `/tests/fixtures/cases/` at grade time.

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (22+ files), `solution/solve.sh` + patch, `tests/test.sh`, `tests/test_outputs.py`, `tests/fixtures/`.

### Test plan
1. `test_schema_version` — report declares schema_version 1.
2. `test_cls_clean_a1_pass` — classification clean row pass with risk ≤25.
3. `test_cls_drift_b4_warn` — drift exception yields warn not fail on calibration slot.
4. `test_reg_exp_c2_warn` — experimental tier regression row warn not pass.
5. `test_reg_baseline_d1_pass` — baseline ratio within band passes.
6. `test_emb_lane_e3_pass` — vector-lane row uses embedding annex not regression.
7. `test_emb_prod_f5_fail` — production tier rejects staging-only warn tolerance.
8. `test_mix_g7_cited_rules` — warn path includes cross-annex cite A3-REG-07.
9. `test_hidden_h1_fail` — hidden case hard fail with cited A1-CLS-02.
10. `test_hidden_h2_risk_cap` — hidden fail risk_score ≥85 with blocking cite bonus.
11. `test_hidden_h3_pass` — hidden regression pass within tightened band.
12. `test_all_matrix_keys_present` — every key in bench_matrix appears in output.

### Drafting guardrails
Instruction stays symptoms-only: no numeric F1/RMSE thresholds, no annex table IDs except where bench row symptoms reference dispute outcomes, no fix-path package names. Opaque symbols `op_bind`, `phase_t2`, `step_k7`. Runbook carries normative numbers; tests embed expected outcomes for named bench keys documented in instruction symptom lines.

### Triviality Ledger

- Hardcoding per-case verdict map passes visible rows but fails hidden fixtures and matrix completeness test.
- Fixing only ingest passes vector-lane row but fails experimental tier and drift downgrade tests.
- Fixing only resolve passes threshold tests but fails cited_rules and risk_score tests.
- Reading archive annex only passes loose regression rows but fails production embedding fail and cls_clean pass tests.

### Per-gate Pitfall Inventory

- RC1 — Oracle patch spans ingest, resolve, and emit; not single-file delete.
- RC6 — Instruction describes reviewer disputes, not annex numbers or fix sites.
- RC7 — solve.sh applies multi-hunk patch ≥40 LOC substantive Go edits.
- CR2 — Flipping contract 4+4+4 tests across j4k, r8n, w3p (cap 4/12).
- CR7 — Instruction nouns banned from fix-path identifiers.
- GX9 — Bench keys named in instruction (`cls_clean_a1`, etc.) have outcomes grounded in symptom prose before tests assert exact verdict strings.
- Static checks — Standard single-step layout, test.sh template verbatim footer.

### Initial Draft Commitments

- `tasks/go-mlops-policy-gate/task.toml`
- `tasks/go-mlops-policy-gate/instruction.md`
- `tasks/go-mlops-policy-gate/output_contract.toml`
- `tasks/go-mlops-policy-gate/environment/Dockerfile`
- `tasks/go-mlops-policy-gate/environment/.dockerignore`
- `tasks/go-mlops-policy-gate/environment/go.mod`
- `tasks/go-mlops-policy-gate/environment/go.sum`
- `tasks/go-mlops-policy-gate/environment/cmd/gatectl/main.go`
- `tasks/go-mlops-policy-gate/environment/core/j4k/ingest.go`
- `tasks/go-mlops-policy-gate/environment/core/r8n/resolve.go`
- `tasks/go-mlops-policy-gate/environment/core/w3p/emit.go`
- `tasks/go-mlops-policy-gate/environment/core/m5q/index.go`
- `tasks/go-mlops-policy-gate/environment/decoy/q2n/reader.go`
- `tasks/go-mlops-policy-gate/environment/decoy/n7f/mdscan.go`
- `tasks/go-mlops-policy-gate/environment/hub/r4v/lookup.go`
- `tasks/go-mlops-policy-gate/environment/lib/run_go.sh`
- `tasks/go-mlops-policy-gate/environment/app/bench_audit.sh`
- `tasks/go-mlops-policy-gate/environment/data/bench_matrix.json`
- `tasks/go-mlops-policy-gate/environment/docs/bench_precedence.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/index.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/part_01.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/part_02.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/part_03.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/part_04.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/part_05.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/part_06.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/annex_a1_cls.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/annex_a2_reg.md`
- `tasks/go-mlops-policy-gate/environment/docs/ops_runbook/annex_a3_emb.md`
- `tasks/go-mlops-policy-gate/environment/docs/archive/legacy_annex.md`
- `tasks/go-mlops-policy-gate/environment/docs/operations_field_notes.md`
- `tasks/go-mlops-policy-gate/environment/config/runtime.toml`
- `tasks/go-mlops-policy-gate/environment/platform/runtime.json`
- `tasks/go-mlops-policy-gate/environment/platform/verifier-requirements.txt`
- `tasks/go-mlops-policy-gate/solution/solve.sh`
- `tasks/go-mlops-policy-gate/solution/gate-fix.patch`
- `tasks/go-mlops-policy-gate/tests/test.sh`
- `tasks/go-mlops-policy-gate/tests/test_outputs.py`
- `tasks/go-mlops-policy-gate/tests/fixtures/cases/hidden_h1.json`
- `tasks/go-mlops-policy-gate/tests/fixtures/cases/hidden_h2.json`
- `tasks/go-mlops-policy-gate/tests/fixtures/cases/hidden_h3.json`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/core/j4k/ingest.go
  symbol: op_bind
  kind: function
  signature: func op_bind(hdr map[string]string) (fam int, err error)
  purpose: Maps report header kind strings to internal family enum for downstream annex selection.

- path: environment/core/r8n/resolve.go
  symbol: phase_t2
  kind: function
  signature: func phase_t2(fam int, tier string, m map[string]float64, annex string) (bands BandSet, err error)
  purpose: Loads threshold bands from annex tables with precedence and tier multipliers.

- path: environment/core/w3p/emit.go
  symbol: step_k7
  kind: function
  signature: func step_k7(b BandSet, m map[string]float64, meta map[string]string) (VerdictRow, error)
  purpose: Computes verdict label, risk_score, cited_rules, and reasons from resolved bands.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/core/j4k/ingest.go
    controls_tests: [test_cls_clean_a1_pass, test_emb_lane_e3_pass, test_hidden_h3_pass, test_all_matrix_keys_present]
  - id: B
    path: environment/core/r8n/resolve.go
    controls_tests: [test_cls_drift_b4_warn, test_reg_exp_c2_warn, test_reg_baseline_d1_pass, test_hidden_h1_fail]
  - id: C
    path: environment/core/w3p/emit.go
    controls_tests: [test_emb_prod_f5_fail, test_mix_g7_cited_rules, test_hidden_h2_risk_cap, test_schema_version]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/decoy/q2n/reader.go
  kind: module
  rhymes_with: phase_t2
  non_fix_purpose: Parses archive markdown for display-only quota hints; never used on eval path.

- path: environment/decoy/n7f/mdscan.go
  kind: helper
  rhymes_with: op_bind
  non_fix_purpose: Tokenizes runbook headings for probe script without binding families.

- path: environment/hub/r4v/lookup.go
  kind: module
  rhymes_with: phase_t2
  non_fix_purpose: Wrong-priority annex lookup used only by deprecated CLI flag.

- path: environment/docs/operations_field_notes.md
  kind: doc
  rhymes_with: bench_precedence
  non_fix_purpose: Field bulletin misdirecting authors to edit archive annex only.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [deployment, gate, runner, scoring, training, submission, bundles, operations, compendium, nightlies, platform, reviewers, classification, accuracy, failures, experimental, tier, regression, submissions, embedding, lane, reports, ceilings, summary, annex, pointers, bench, audit, rebuild, output, verdicts, matrix, metric, slots, normative, bands, cross, exceptions, vector, schema, cases, verdict, pass, warn, fail, risk, score, cited, rules, reasons, calibration, baseline, ratio, production, staging, tolerance, reviewers, dispute, drift, downgrade, headlines, inherit, pointers, runner, gatectl, bench_audit, bench_verdicts, bench_matrix, ops_runbook, bench_precedence]
```
