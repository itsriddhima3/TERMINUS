### Decision
GO — Attempt 1. Embedded C telemetry recorder on SQLite 3.43 WAL with deterministic mid-cycle power-cut harness; opaque fix symbols across store open, cycle checkpoint, and shutdown finalize modules; twelve verifier tests with flipping-point coverage.

### Metadata
- version: 2
- Task name: c-sqlite-wal-powerloss
- Title: WAL Powerloss Recovery
- Category: debugging
- Languages: ["c", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific", "db_interaction"]
- Tags: ["sqlite", "wal", "embedded", "c", "durability", "recovery"]
- Milestones: 0

## Authoring Brief

### Public contract
Field devices run `/app/bin/datalog` against flash-resident catalogs opened in write-ahead logging mode. Operators rebuild from `/app/src` and run `/app/bin/datalog audit --output /app/output/recovery_report.json`. The audit executes the bundled crash suite from `/app/data/crash_manifest.toml` and must emit JSON whose `scenarios[]` entries each show `recovered` true, `integrity_ok` true, row counts matching `/app/docs/field_matrix.md` for kits KIT-A through KIT-D, and `schema_marker` 2. Summary `all_recovered` must be true. Normative durability semantics live under `/app/docs/catalog/`; `/app/docs/bench_precedence.md` outranks archive notes.

### Failure topology
After abrupt power loss during the nightly compaction window, reopened catalogs throw schema errors or return zero rows despite intact main files. Symptoms cluster around open-time pragma profile, mid-cycle frame consolidation, and finalize ordering before handle teardown. Decoy sync helpers and field bulletins suggest vacuum or journal-mode toggles; real defects sit in store bootstrap, maintenance cycle driver, and cycle finalizer coupling.

### Environment shape
Dockerized C project at `/app`: SQLite 3.43 amalgamation built at image time, `datalog` CLI, opaque modules under `src/store`, `src/maint`, seed CSVs, crash manifest, scattered catalog memos, bash build script. Verifier rebuilds via `/app/scripts/build.sh`, runs audit subprocess, parses recovery report JSON.

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (20+ files), `solution/solve.sh`, `tests/{test.sh, test_outputs.py}`.

### Test plan
Twelve tests: report exists; four scenario recovered flags; four integrity_ok flags; four row_count vs field_matrix; schema_marker 2 per scenario; summary all_recovered; audit_digest stable; NOP rejects partial fix (sync-only); catalog fingerprint stable across reruns; bravo kit boundary row count; delta kit post-crash query smoke.

### Drafting guardrails
Instruction stays symptoms-only: no API flag names, no pragma literals, no fix-path symbol names. Opaque identifiers on fix path. Decoys perform genuine ancillary reads. Expected row counts grounded in field_matrix.md before tests assert them.

### Triviality Ledger

- K2 class-2 sync alone passes integrity on clean shutdown but fails P8 dimension (residual sidecar bytes) because merge stays pass-through.
- P8 truncate merge alone passes bravo charlie sidecar checks but fails Q1 dimension (empty sync stamp) and K2 dimension (sync class 0).
- Q1 directory barrier + stamp alone passes marker tests but fails K2 dimension and leaves residual frames under abrupt stop.
- VACUUM decoy path (field bulletin 07) shrinks file size but fails every integrity and sidecar assertion.

### Hardness axes (A0)

| Axis | How the task satisfies it |
|------|---------------------------|
| Discover | Subsystem codes K2/P8/Q1 live only in catalog memos + bench_profiles.toml; fix paths use opaque symbols (`op_k2`, `phase_p8`, `step_q1`) in separate module roots (`gate/`, `src/maint/`, `journal/`). |
| Synthesize | Audit `recovered` requires all three dimensions (sync class, sidecar clear, sync stamp) — partial patches fail distinct test clusters. |
| Diagnose | Instruction is symptoms-only; agents must run audit stderr + `cycle_diag.sh` to see k2_dim/p8_dim/q1_dim failures, then map to catalog/bench_profiles. |
| Navigate coupling | Open bundle, merge driver, and finalize seal are in non-adjacent trees; decoys push VACUUM/passive merge misdirection. |
| Reason beyond training | SQLite 3.43 WAL checkpoint truncate semantics, synchronous FULL + fullfsync, directory fsync before handle close — niche embedded durability, not generic CRUD. |

### Per-gate Pitfall Inventory

- RC1 — Oracle patches store open, cycle checkpoint, and finalize modules; not a one-line pragma revert.
- RC6 — Instruction describes field symptoms and output contract, not C API symbols.
- RC7 — Combined solve.sh substantive C edits ≥40 LOC.
- CR2 — Flipping contract splits op_k2, phase_p8, step_q1 across 4+4+4 tests (max 4/12).
- CR7 — Instruction nouns banned from fix-path identifiers.
- GX9 — KIT row counts and schema_marker grounded in field_matrix.md / instruction before tests assert.
- Static checks — standard test_outputs.py, canonical test.sh template.

### Initial Draft Commitments

- `tasks/c-sqlite-wal-powerloss/task.toml`
- `tasks/c-sqlite-wal-powerloss/output_contract.toml`
- `tasks/c-sqlite-wal-powerloss/instruction.md`
- `tasks/c-sqlite-wal-powerloss/environment/Dockerfile`
- `tasks/c-sqlite-wal-powerloss/environment/.dockerignore`
- `tasks/c-sqlite-wal-powerloss/environment/Makefile`
- `tasks/c-sqlite-wal-powerloss/environment/include/datalog.h`
- `tasks/c-sqlite-wal-powerloss/environment/include/store_iface.h`
- `tasks/c-sqlite-wal-powerloss/environment/include/maint_iface.h`
- `tasks/c-sqlite-wal-powerloss/environment/src/main.c`
- `tasks/c-sqlite-wal-powerloss/environment/src/audit_run.c`
- `tasks/c-sqlite-wal-powerloss/environment/src/store/op_k2.c`
- `tasks/c-sqlite-wal-powerloss/environment/src/store/op_n4.c`
- `tasks/c-sqlite-wal-powerloss/environment/src/maint/phase_p8.c`
- `tasks/c-sqlite-wal-powerloss/environment/src/maint/step_q1.c`
- `tasks/c-sqlite-wal-powerloss/environment/src/maint/op_r3.c`
- `tasks/c-sqlite-wal-powerloss/environment/src/ingest/load_seed.c`
- `tasks/c-sqlite-wal-powerloss/environment/src/util/fs_sync.c`
- `tasks/c-sqlite-wal-powerloss/environment/src/util/log_x1.c`
- `tasks/c-sqlite-wal-powerloss/environment/decoy/sync_stub.c`
- `tasks/c-sqlite-wal-powerloss/environment/decoy/wal_reader.c`
- `tasks/c-sqlite-wal-powerloss/environment/decoy/checkpoint_ui.c`
- `tasks/c-sqlite-wal-powerloss/environment/scripts/build.sh`
- `tasks/c-sqlite-wal-powerloss/environment/scripts/init_workspace.sh`
- `tasks/c-sqlite-wal-powerloss/environment/config/runtime.toml`
- `tasks/c-sqlite-wal-powerloss/environment/platform/runtime.json`
- `tasks/c-sqlite-wal-powerloss/environment/data/crash_manifest.toml`
- `tasks/c-sqlite-wal-powerloss/environment/data/seeds/KIT-A.csv`
- `tasks/c-sqlite-wal-powerloss/environment/data/seeds/KIT-B.csv`
- `tasks/c-sqlite-wal-powerloss/environment/data/seeds/KIT-C.csv`
- `tasks/c-sqlite-wal-powerloss/environment/data/seeds/KIT-D.csv`
- `tasks/c-sqlite-wal-powerloss/environment/docs/field_matrix.md`
- `tasks/c-sqlite-wal-powerloss/environment/docs/storage_contract.md`
- `tasks/c-sqlite-wal-powerloss/environment/docs/compaction_window.md`
- `tasks/c-sqlite-wal-powerloss/environment/docs/bench_precedence.md`
- `tasks/c-sqlite-wal-powerloss/environment/docs/archive/legacy_wal_notes.md`
- `tasks/c-sqlite-wal-powerloss/environment/docs/ops/field_bulletin_07.md`
- `tasks/c-sqlite-wal-powerloss/environment/docs/catalog/part_01_open.md`
- `tasks/c-sqlite-wal-powerloss/environment/docs/catalog/part_02_cycle.md`
- `tasks/c-sqlite-wal-powerloss/environment/schemas/recovery_report.example.json`
- `tasks/c-sqlite-wal-powerloss/environment/ops/retention_policy.txt`
- `tasks/c-sqlite-wal-powerloss/environment/harness/ci_stub.txt`
- `tasks/c-sqlite-wal-powerloss/tests/test.sh`
- `tasks/c-sqlite-wal-powerloss/tests/test_outputs.py`
- `tasks/c-sqlite-wal-powerloss/solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/src/store/op_k2.c
  symbol: apply_open_flags
  kind: function
  signature: int apply_open_flags(sqlite3 *db, int profile)
  purpose: Applies open-time pragma bundle for catalog handle before ingest.

- path: environment/src/maint/phase_p8.c
  symbol: run_cycle_check
  kind: function
  signature: int run_cycle_check(sqlite3 *db, int mode_hint)
  purpose: Consolidates write-ahead frames into main file during maintenance cycle.

- path: environment/src/maint/step_q1.c
  symbol: finalize_cycle
  kind: function
  signature: int finalize_cycle(sqlite3 *db, const char *dir_path)
  purpose: Completes cycle teardown including directory durability before close.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/src/store/op_k2.c
    controls_tests: [test_alpha_recovered, test_bravo_recovered, test_alpha_integrity, test_bravo_row_count, test_schema_marker_alpha, test_schema_marker_bravo]
  - id: B
    path: environment/src/maint/phase_p8.c
    controls_tests: [test_charlie_recovered, test_delta_recovered, test_charlie_integrity, test_delta_integrity, test_schema_marker_charlie, test_schema_marker_delta]
  - id: C
    path: environment/src/maint/step_q1.c
    controls_tests: [test_summary_all_recovered, test_audit_digest_stable, test_delta_query_smoke, test_catalog_fingerprint_stable]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/decoy/sync_stub.c
  kind: module
  rhymes_with: apply_open_flags
  non_fix_purpose: Display-only pragma preview for probe script; never linked on open path.

- path: environment/decoy/checkpoint_ui.c
  kind: helper
  rhymes_with: run_cycle_check
  non_fix_purpose: Parses manifest for UI totals without invoking consolidation API.

- path: environment/docs/ops/field_bulletin_07.md
  kind: doc
  rhymes_with: bench_precedence
  non_fix_purpose: Misdirects operators toward vacuum and analyze instead of cycle driver fixes.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [field, devices, datalog, flash, catalogs, write-ahead, logging, operators, rebuild, audit, output, recovery, report, scenarios, recovered, integrity, row, counts, kits, matrix, summary, compaction, window, schema, marker, downstream, sync, rejects, device, unserviceable, power, loss, abrupt, stop, mid-cycle, nightly, malformed, reader, queries, telemetry, recorder, durability, semantics, bench, precedence, archive, notes, crash, suite, manifest, seeds, bravo, charlie, delta, alpha, integrity_ok, all_recovered, audit_digest, catalog, fingerprint, query, smoke, maintenance, cycle, finalize, consolidate, frames, pragma, profile, ingest, teardown, handle, close, directory, storage, contract, compaction, embedded, sqlite, wal, powerloss]
```
