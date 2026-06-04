### Decision
GO — Attempt 1. Spring Boot NDJSON meter pipeline with three coupled CLI stages, distributed fix surface across fetch/normalize/reconcile, and local API + CSV join complexity.

### Metadata
- version: 2
- Task name: java-meter-ndjson-reconcile
- Title: Java Meter NDJSON Reconciler
- Category: data-processing
- Languages: ["java", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["api_integration"]
- Tags: ["java", "spring-boot", "ndjson", "meter", "cli", "api"]
- Milestones: 3

## Authoring Brief

### Public contract
Build `/app/bin/meterctl` (Java CLI) against a local Spring Boot smart-meter API on port 8080. Three subcommands for batch `MTR-2024-Q1`: `fetch` persists paginated NDJSON readings to `/app/var/readings.json`; `normalize` joins `/app/data/devices.csv` and `/app/data/tariffs.csv`, applies correction events from the API, writes `/app/var/normalized.json`; `reconcile` emits `/app/output/reconcile.json` and `/app/output/normalized.csv` flagging interval gaps, duplicate timestamps, and impossible register deltas with `cost_by_site` roll-ups.

### Failure topology
Fetch stage drops paginated rows, mangles UTC timestamps, and reverses stream order. Normalize mis-joins device catalog rows, picks wrong tariff windows, and ignores correction deltas. Reconcile under-detects gaps (30-minute skip on DEV-A02), duplicates (same timestamp, different register), and impossible deltas (DEV-B01 +1.5 kWh vs 1.0 limit). Docs under `/app/docs/` disagree on pagination, window bounds, and delta thresholds — bench precedence resolves conflicts.

### Environment shape
Shared `environment/`: Spring Boot API (`api/`), Java CLI (`cli/`), CSV inputs (`data/`), policy TOML (`config/`), operator docs (`docs/`), decoy helpers (`decoy/`), build/start scripts (`scripts/`), platform verifier pins (`platform/`). Milestone content under `steps/milestone_{1,2,3}/`.

### Required artifacts
Milestone layout per `task-creation.mdc`: `task.toml` v2.0 with three `[[steps]]`, `output_contract.toml`, `environment/Dockerfile`, 20+ env files, per-milestone `instruction.md`, `tests/{test.sh, test_mN.py}`, `solution/{solve.sh, solveN.sh, patches/}`.

### Test plan
M1 (15 tests): eight readings in stream order, UTC Z suffix, schema, pagination page-two rows, idempotent fetch. M2 (17 tests): site_id/rate_cents/max_delta, correction-adjusted registers, tariff window exclusivity, preserves fetch columns. M3 (22 tests): gap DEV-A02 expected_at 00:15, duplicate DEV-A01 00:30, impossible delta DEV-B01 00:15, cost_by_site totals, CSV issue column bijection with JSON events.

### Drafting guardrails
Opaque fix-path symbols (`op_fetch_c`, `op_join_d`, …). No instruction nouns in code symbols. Expected values embedded in tests, not env golden files. Symptoms-only milestone instructions with signal-completion directive.

### Triviality Ledger
- Pagination-only fetch passes count test but fails page-two device rows — blocked by per-row device assertions.
- Reversing row order passes count but fails stream-order checksum — blocked by ordered digest test.
- Fixing device join alone passes site_id on some rows but fails correction keys — blocked by corrected_register assertions tied to API delta.
- Tightening duplicate detection by register value alone misses timestamp collisions — blocked by DEV-A01 00:30 pair with different registers.

### Per-gate Pitfall Inventory
- RC1: Oracle patches add pagination loop and missingSlot helper, not deletions.
- RC3: Tests assert computed gap/duplicate/delta/cost values, not file existence.
- RC6: Instructions describe wrong outputs, not patch sites or algorithm names.
- RC7: Nine patch hunks across seven Java files exceed 30 LOC substantive delta.
- CR1/CR7: symbol_table names used verbatim on fix path; no `meterctl`/`fetch`/`gap` function names.
- GX9: Test literals for MTR-2024-Q1, DEV-A01, eight readings grounded in milestone_1 instruction.

### Initial Draft Commitments
- `tasks/java-meter-ndjson-reconcile/task.toml`
- `tasks/java-meter-ndjson-reconcile/output_contract.toml`
- `tasks/java-meter-ndjson-reconcile/environment/Dockerfile`
- `tasks/java-meter-ndjson-reconcile/environment/api/**` (Spring Boot + fixtures)
- `tasks/java-meter-ndjson-reconcile/environment/cli/**` (meter package)
- `tasks/java-meter-ndjson-reconcile/environment/config/**`
- `tasks/java-meter-ndjson-reconcile/environment/data/devices.csv`
- `tasks/java-meter-ndjson-reconcile/environment/data/tariffs.csv`
- `tasks/java-meter-ndjson-reconcile/environment/decoy/**`
- `tasks/java-meter-ndjson-reconcile/environment/docs/**`
- `tasks/java-meter-ndjson-reconcile/environment/scripts/**`
- `tasks/java-meter-ndjson-reconcile/steps/milestone_1/**`
- `tasks/java-meter-ndjson-reconcile/steps/milestone_2/**`
- `tasks/java-meter-ndjson-reconcile/steps/milestone_3/**`
- `specs/java-meter-ndjson-reconcile-rubrics.txt`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: cli/src/main/java/meter/ingest/NdjsonFetch.java
  symbol: op_fetch_c
  kind: function
  signature: op_fetch_c(String a)
  purpose: paginate NDJSON stream pages via cursor header
- path: cli/src/main/java/meter/ingest/TsNorm.java
  symbol: op_norm_b
  kind: function
  signature: op_norm_b(String a)
  purpose: preserve UTC timestamp suffix on parse
- path: cli/src/main/java/meter/ingest/CsvLookup.java
  symbol: op_join_d
  kind: function
  signature: op_join_d(Path a)
  purpose: index device catalog rows by device id
- path: cli/src/main/java/meter/join/TariffWin.java
  symbol: op_tariff_f
  kind: function
  signature: op_tariff_f(List<TariffRow> a, String b, String c)
  purpose: select tariff rate with exclusive window end
- path: cli/src/main/java/meter/app/NormalizeCmd.java
  symbol: run
  kind: function
  signature: run(String a)
  purpose: apply correction delta to corrected register field
- path: cli/src/main/java/meter/recon/GapDetect.java
  symbol: op_gap_g
  kind: function
  signature: op_gap_g(List<Map<String,Object>> a, int b)
  purpose: emit gap events when span exceeds interval
- path: cli/src/main/java/meter/recon/DupDetect.java
  symbol: op_dup_h
  kind: function
  signature: op_dup_h(List<Map<String,Object>> a)
  purpose: flag duplicate device_id+reading_at keys
- path: cli/src/main/java/meter/recon/DeltaCheck.java
  symbol: op_delta_i
  kind: function
  signature: op_delta_i(List<Map<String,Object>> a)
  purpose: compare corrected register deltas to max_delta limit
- path: cli/src/main/java/meter/recon/ReportEmit.java
  symbol: op_emit_k
  kind: function
  signature: op_emit_k(Path jsonOut, Path csvOut, ReconBody a, List<Map<String,Object>> b)
  purpose: tag CSV gap rows using post-gap reading_at key

#### flipping_point_contract
locations:
  - id: A
    path: cli/src/main/java/meter/ingest/NdjsonFetch.java
    controls_tests: [test_m1_reading_count, test_m1_stream_order, test_m1_page_two_dev_b01]
  - id: B
    path: cli/src/main/java/meter/ingest/CsvLookup.java
    controls_tests: [test_m2_site_north_dev_a01, test_m2_max_delta_dev_b01, test_m2_tariff_rate_north_midnight]
  - id: C
    path: cli/src/main/java/meter/recon/GapDetect.java
    controls_tests: [test_m3_gap_dev_a02, test_m3_csv_gap_issue_a02]
  - id: D
    path: cli/src/main/java/meter/recon/DupDetect.java
    controls_tests: [test_m3_duplicate_dev_a01, test_m3_csv_duplicate_rows]
  - id: E
    path: cli/src/main/java/meter/recon/DeltaCheck.java
    controls_tests: [test_m3_impossible_dev_b01, test_m3_csv_impossible_issue]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: decoy/NdjsonStub.java
  kind: helper
  rhymes_with: op_parse_a
  non_fix_purpose: validates NDJSON line shape for logging only
- path: decoy/IntervalLedger.java
  kind: helper
  rhymes_with: op_gap_g
  non_fix_purpose: aggregates interval counts for audit summaries without gap detection

#### code_forbidden_tokens
code_forbidden_tokens: [meter, readings, normalize, fetch, spring, ndjson, tariff, device, gap, duplicate, delta, reconciliation, register, timestamp, paginated, stream, correction, csv, json, site, interval, impossible, cost, batch, api, cli, spring-boot, smart-meter, meterctl, normalized, reconcile]
