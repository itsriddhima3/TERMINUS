### Decision
GO — Attempt 1. Rust clip ingest desk with rusqlite cache and ffprobe lane; concurrent stress exposes lock storms; opaque fix symbols across store bootstrap, write lane pool, and ingest retry modules; twelve verifier tests with flipping-point coverage.

### Metadata
- version: 2
- Task name: rust-ffmpeg-probe-cache
- Title: Probe Cache Contention
- Category: debugging
- Languages: ["rust", "sql", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific", "db_interaction"]
- Tags: ["rust", "rusqlite", "ffmpeg", "sqlite", "concurrency", "ingest"]
- Milestones: 0

## Authoring Brief

### Public contract
Operators rebuild `/app/bin/clipvault` from the crate tree and run `/app/bin/clipvault stress --manifest /app/data/stress_manifest.toml --output /app/output/stress_ledger.json`. The stress harness fans out parallel workers over clips listed in the manifest. The ledger JSON must match `/app/docs/ingest_contract.md` (per-lane `observed_rows`, `busy_events`, `journal_mode`, `integrity_ok`, plus `summary.all_complete`). Row totals must match `/app/docs/lane_matrix.md` for lanes LANE-A through LANE-D. Normative lane semantics live under `/app/docs/catalog/`; `/app/docs/bench_precedence.md` outranks archive bulletins.

### Failure topology
Under parallel ingest, workers interleave stream fact writes into per-lane sqlite catalogs. Symptoms cluster as stderr lock errors, ledger gaps (`observed_rows` below matrix), nonzero `busy_events`, and ledgers reporting `delete` journal family despite WAL tokens appearing in source. Root causes are **non-obvious**: K2 applies WAL then a second pragma batch downgrades family; Q3 ships pool crates but uses a process-wide shared handle without per-insert transactions; P2 advertises retry but only performs two 1ms sleeps. Agents must traverse rubric → bench_profiles numerics → three crate roots (k9m/r2n/p4v). Archive notes and bulletin 09 misdirect toward busy_timeout-only or VACUUM fixes.

### Environment shape
Dockerized Rust workspace at `/app`: `clipvault` binary (ffprobe + rusqlite), opaque modules under `clipvault/src/store`, `clipvault/src/pool`, `clipvault/src/ingest`, tiny generated clips, stress manifest, scattered catalog memos, bash build script. Verifier rebuilds via `/app/scripts/build.sh`, runs stress subprocess, parses ledger JSON and spot-checks lane DB files.

### Required artifacts
Standard layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (20+ files), `solution/solve.sh`, `tests/{test.sh, test_outputs.py}`, `construction_manifest.json`.

### Test plan
Twelve tests: stress exit zero; four lane observed_rows vs matrix; four busy_events zero; four integrity_ok; four journal_mode wal; summary all_complete; ledger digest stable; NOP rejects pool-only patch; lane alpha concurrent read smoke; delta lane duration checksum field.

### Drafting guardrails
Instruction stays symptoms-only: no pragma names, no pool API names, no retry recipe, no fix-path symbol names. Opaque identifiers on fix path. Decoys perform genuine ancillary reads. Matrix row counts grounded in lane_matrix.md before tests assert them.

### Triviality Ledger

- M7 bootstrap-only patch enables wal journal but shared-handle lane still serializes writers — bravo/charlie rows stay short and busy_events remain high.
- Q3 pool-only patch without transactional batching still loses rows under parallel insert — alpha/delta observed_rows fail while journal_mode may read wal.
- P2 retry-only patch reduces busy_events but DELETE journal and single connection still cap throughput — integrity or row totals fail on charlie/delta lanes.
- Decoy vacuum bulletin shrinks file size but fails every row and busy assertion.

### Per-gate Pitfall Inventory

- RC1 — Oracle rewrites store bootstrap, write lane pool, and ingest retry modules; not a one-line pragma sed on a comment.
- RC6 — Instruction describes lock storms and ledger gaps, not rusqlite API symbols.
- RC7 — Combined solve.sh substantive Rust edits ≥40 LOC across three modules.
- CR2 — Flipping contract splits op_m7, lane_q3, op_p2 across 4+4+4 tests (max 4/12).
- CR7 — Instruction nouns banned from fix-path identifiers.
- GX9 — Lane row counts grounded in lane_matrix.md / ingest_contract before tests assert.
- Static checks — standard test_outputs.py, canonical test.sh template.

### Initial Draft Commitments

- `tasks/rust-ffmpeg-probe-cache/task.toml`
- `tasks/rust-ffmpeg-probe-cache/output_contract.toml`
- `tasks/rust-ffmpeg-probe-cache/instruction.md`
- `tasks/rust-ffmpeg-probe-cache/construction_manifest.json`
- `tasks/rust-ffmpeg-probe-cache/environment/Dockerfile`
- `tasks/rust-ffmpeg-probe-cache/environment/.dockerignore`
- `tasks/rust-ffmpeg-probe-cache/environment/Cargo.toml`
- `tasks/rust-ffmpeg-probe-cache/environment/clipvault/Cargo.toml`
- `tasks/rust-ffmpeg-probe-cache/environment/clipvault/src/main.rs`
- `tasks/rust-ffmpeg-probe-cache/environment/clipvault/src/lib.rs`
- `tasks/rust-ffmpeg-probe-cache/environment/clipvault/src/cmd/stress.rs`
- `tasks/rust-ffmpeg-probe-cache/environment/clipvault/src/store/op_m7.rs`
- `tasks/rust-ffmpeg-probe-cache/environment/clipvault/src/pool/lane_q3.rs`
- `tasks/rust-ffmpeg-probe-cache/environment/clipvault/src/ingest/op_p2.rs`
- `tasks/rust-ffmpeg-probe-cache/environment/clipvault/src/probe/ff_lane.rs`
- `tasks/rust-ffmpeg-probe-cache/environment/decoy/read_lane.rs`
- `tasks/rust-ffmpeg-probe-cache/environment/decoy/sync_hint.rs`
- `tasks/rust-ffmpeg-probe-cache/environment/scripts/build.sh`
- `tasks/rust-ffmpeg-probe-cache/environment/scripts/init_workspace.sh`
- `tasks/rust-ffmpeg-probe-cache/environment/scripts/gen_clips.sh`
- `tasks/rust-ffmpeg-probe-cache/environment/config/runtime.toml`
- `tasks/rust-ffmpeg-probe-cache/environment/config/bench_profiles.toml`
- `tasks/rust-ffmpeg-probe-cache/environment/data/stress_manifest.toml`
- `tasks/rust-ffmpeg-probe-cache/environment/docs/ingest_contract.md`
- `tasks/rust-ffmpeg-probe-cache/environment/docs/lane_matrix.md`
- `tasks/rust-ffmpeg-probe-cache/environment/docs/bench_precedence.md`
- `tasks/rust-ffmpeg-probe-cache/environment/docs/catalog/part_01_open.md`
- `tasks/rust-ffmpeg-probe-cache/environment/docs/catalog/part_02_write.md`
- `tasks/rust-ffmpeg-probe-cache/environment/docs/catalog/part_03_lane.md`
- `tasks/rust-ffmpeg-probe-cache/environment/docs/ops/bulletin_09.md`
- `tasks/rust-ffmpeg-probe-cache/environment/docs/archive/legacy_journal_notes.md`
- `tasks/rust-ffmpeg-probe-cache/environment/schemas/stress_ledger.example.json`
- `tasks/rust-ffmpeg-probe-cache/environment/ops/retention_policy.txt`
- `tasks/rust-ffmpeg-probe-cache/environment/harness/ci_stub.txt`
- `tasks/rust-ffmpeg-probe-cache/environment/platform/runtime.json`
- `tasks/rust-ffmpeg-probe-cache/environment/README.md`
- `tasks/rust-ffmpeg-probe-cache/tests/test.sh`
- `tasks/rust-ffmpeg-probe-cache/tests/test_outputs.py`
- `tasks/rust-ffmpeg-probe-cache/solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/clipvault/src/store/op_m7.rs
  symbol: apply_open_bundle
  kind: function
  signature: pub fn apply_open_bundle(conn: &rusqlite::Connection) -> rusqlite::Result<()>
  purpose: Applies catalog open-time pragma bundle before lane ingest.

- path: environment/clipvault/src/pool/lane_q3.rs
  symbol: with_lane_tx
  kind: function
  signature: pub fn with_lane_tx<F, T>(db_path: &std::path::Path, workers: usize, f: F) -> rusqlite::Result<T> where F: Fn(&rusqlite::Connection) -> rusqlite::Result<T> + Send + Sync, T: Send
  purpose: Acquires pooled catalog handle and runs caller body inside a write transaction.

- path: environment/clipvault/src/ingest/op_p2.rs
  symbol: persist_row
  kind: function
  signature: pub fn persist_row(conn: &rusqlite::Connection, clip_key: &str, dur_ms: i64, stream_hash: &str) -> rusqlite::Result<()>
  purpose: Inserts one probe row into lane catalog with contention handling.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/clipvault/src/store/op_m7.rs
    controls_tests: [test_lane_alpha_rows, test_lane_bravo_rows, test_lane_alpha_integrity, test_lane_bravo_journal_wal, test_lane_alpha_journal_wal, test_lane_bravo_integrity]
  - id: B
    path: environment/clipvault/src/pool/lane_q3.rs
    controls_tests: [test_lane_charlie_rows, test_lane_delta_rows, test_lane_charlie_integrity, test_lane_delta_integrity, test_lane_charlie_journal_wal, test_lane_delta_journal_wal]
  - id: C
    path: environment/clipvault/src/ingest/op_p2.rs
    controls_tests: [test_stress_exit_success, test_summary_all_complete, test_lane_alpha_busy_zero, test_lane_bravo_busy_zero, test_lane_charlie_busy_zero, test_lane_delta_busy_zero]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/decoy/read_lane.rs
  kind: module
  rhymes_with: apply_open_bundle
  non_fix_purpose: Read-only pragma preview for diagnostics script without mutating catalogs.

- path: environment/decoy/sync_hint.rs
  kind: helper
  rhymes_with: with_lane_tx
  non_fix_purpose: Parses manifest totals for CI banner without opening write pool.

- path: environment/docs/ops/bulletin_09.md
  kind: doc
  rhymes_with: bench_precedence
  non_fix_purpose: Misdirects operators toward vacuum instead of lane write coupling fixes.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [clip, ingest, desk, workers, catalogue, streams, clips, rebuild, clipvault, crate, stress, manifest, output, ledger, load, stderr, database, locked, incomplete, lanes, totals, matrix, contract, observed, busy, journal, integrity, summary, complete, concurrent, readers, operators, parallel, stream, facts, sqlite, catalogs, lock, errors, gaps, events, profiles, writers, vacuum, single-writer, bootstrap, pragmas, handle, persistence, retry, policy, normative, semantics, archive, bulletins, lane, alpha, bravo, charlie, delta, harness, fans, listed, per-lane, integrity_check, write-ahead]
```
