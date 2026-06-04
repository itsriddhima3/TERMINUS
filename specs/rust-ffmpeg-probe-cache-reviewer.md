### Decision
GO — Attempt 1. Same as authoring spec.

### Metadata
- Task name: rust-ffmpeg-probe-cache
- Title: Probe Cache Contention
- Category: debugging
- Languages: ["rust", "sql", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["tool_specific", "db_interaction"]
- Tags: ["rust", "rusqlite", "ffmpeg", "sqlite", "concurrency", "ingest"]
- Milestones: 0

### Discovery budget
- Discovery: bench_profiles.toml maps subsystem codes m7/q3/p2 to k9m/r2n/p4v modules — not named in instruction.md
  Planned location: environment/config/bench_profiles.toml
  Why hidden: instruction points at runtime.toml and ingest_contract only
- Discovery: shared static connection in r2n/q3_wire causes parallel write loss — symptom is row gaps not "use pool"
  Planned location: environment/r2n/q3_wire.rs
  Why hidden: instruction describes ledger gaps, not single-handle design
- Discovery: busy counter meta key increments on failed persist without retry backoff
  Planned location: environment/p4v/op_p2.rs
  Why hidden: instruction mentions elevated contention counters, not retry policy location

### Topology enumeration (3 candidate fix topologies)
1. Open-bundle + write-scope + persist retry (shipped): k9m/op_m7.rs + r2n/q3_wire.rs + p4v/op_p2.rs — all three required.
2. Open-bundle + persist retry only: WAL helps but single-handle q3 still drops rows under par_iter.
3. Write-scope + persist retry only: pool/tx without WAL still sees lock storms and non-wal journal_mode.

### Collapse verdict: PASS (WARN on GX7/GX9 borderline — ingest_contract homes work_root; field requirements delegated to contract doc)
