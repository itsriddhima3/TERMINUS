### Decision
GO — Attempt 1. Long-context Rust unsafe offset task with Miri matrix verification across three distributed helper modules.

### Metadata
- version: 2
- Task name: unsafe-offset-invariant
- Title: Unsafe Offset Invariant
- Category: debugging
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context", "tool_specific"]
- Tags: ["rust", "unsafe", "miri", "memory-safety", "debugging"]
- Milestones: 0

## Authoring Brief

### Public contract
Agent receives a Rust workspace implementing a probabilistic multi-level ordered map with unsafe internal helpers, a ~120-page Rustonomicon-style corpus under `/app/docs/rustonomicon/`, and `/app/app/matrix_audit.sh` writing `/app/output/audit_report.json`. Broken state passes plain `cargo test` but Miri flags undefined behavior on matrix seeds. Repair must preserve public API hash and signatures; acceptance bands live in `/app/data/scenario_matrix.json`.

### Failure topology
Three unsafe helpers treat node addresses as inline pointer arrays or offset into forward buffers without bounds/provenance checks. Symptoms cluster on insert-heavy and high-band scenarios while smoke tests pass under rustc alone.

### Environment shape
Dockerized Rust nightly workspace with Miri, tower_store crate split across core/arena/chain/seq/api/rng modules, generated reference corpus, Python matrix runner, bash audit entrypoint, decoy helpers.

### Required artifacts
Standard single-step layout with 34+ environment files, generated chapter corpus at build, six Miri integration scenarios, pytest outcome verifier.

### Test plan
Eighteen tests: report schema fields, checker_clean, per-scenario pass status, corpus chapter 8 presence, API hash unchanged, decoy modules present.

### Triviality Ledger
- Fixing only lookup helper passes zeta collect path but fails insert-heavy gamma/epsilon under Miri.
- Replacing unsafe with safe wrappers everywhere fails API hash / signature constraints.
- Disabling Miri in runner passes JSON shape tests but fails checker_clean and scenario status assertions.

### Per-gate Pitfall Inventory
- RC6: instruction names output fields and paths, not chapter numbers or helper symbols.
- CR2: fix split across arena/p2, chain/r4, core/w8 with per-scenario flip tests.
- GX9: numeric pass counts referenced via scenario_matrix.json not recited per seed in instruction.

### Initial Draft Commitments
- tasks/unsafe-offset-invariant/instruction.md
- tasks/unsafe-offset-invariant/task.toml
- tasks/unsafe-offset-invariant/output_contract.toml
- tasks/unsafe-offset-invariant/construction_manifest.json
- tasks/unsafe-offset-invariant/environment/Dockerfile
- tasks/unsafe-offset-invariant/environment/Cargo.toml
- tasks/unsafe-offset-invariant/environment/rust-toolchain.toml
- tasks/unsafe-offset-invariant/environment/crates/tower_store/** 
- tasks/unsafe-offset-invariant/environment/docs/**
- tasks/unsafe-offset-invariant/environment/data/scenario_matrix.json
- tasks/unsafe-offset-invariant/environment/tools/{gen_docs.py,run_matrix.sh}
- tasks/unsafe-offset-invariant/environment/app/matrix_audit.sh
- tasks/unsafe-offset-invariant/environment/config/**
- tasks/unsafe-offset-invariant/environment/lib/cargo_helpers.sh
- tasks/unsafe-offset-invariant/environment/bench/README.md
- tasks/unsafe-offset-invariant/environment/migrations/README.md
- tasks/unsafe-offset-invariant/environment/v/**
- tasks/unsafe-offset-invariant/solution/solve.sh
- tasks/unsafe-offset-invariant/tests/{test.sh,test_outputs.py}

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: crates/tower_store/src/arena/p2.rs
  symbol: op_k
  kind: function
  signature: pub unsafe fn op_k(n: *mut Node, lvl: usize) -> *mut Node
  purpose: reads outbound edge at elevation from node tower buffer
- path: crates/tower_store/src/chain/r4.rs
  symbol: step_m
  kind: function
  signature: pub unsafe fn step_m(n: *mut Node, lvl: usize) -> *mut Node
  purpose: advances one hop at elevation during lookup walks
- path: crates/tower_store/src/core/w8.rs
  symbol: bind_q
  kind: function
  signature: pub unsafe fn bind_q(head: *mut Node, h: usize, cap: usize) -> *mut Node
  purpose: resolves cursor link at band during insert path
```

#### flipping_point_contract

```
locations:
  - id: A
    path: crates/tower_store/src/arena/p2.rs
    controls_tests: [test_scenario_gamma_pass, test_scenario_epsilon_pass, test_scenario_pass_count, test_checker_clean]
  - id: B
    path: crates/tower_store/src/chain/r4.rs
    controls_tests: [test_scenario_alpha_pass, test_scenario_zeta_pass, test_api_surface_hash, test_public_api_hash_unchanged]
  - id: C
    path: crates/tower_store/src/core/w8.rs
    controls_tests: [test_scenario_beta_pass, test_scenario_delta_pass, test_each_scenario_passes, test_scenario_total]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: crates/tower_store/src/arena/d3.rs
  kind: helper
  rhymes_with: op_k
  non_fix_purpose: bounded tower diagnostics with validated indexing
- path: crates/tower_store/src/chain/n1.rs
  kind: helper
  rhymes_with: step_m
  non_fix_purpose: band-zero walks using safe field access
- path: environment/v/v9_decoy.rs
  kind: module
  rhymes_with: bind_q
  non_fix_purpose: layout probe constants unrelated to store logic
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [tower, store, workspace, probabilistic, multi, level, ordered, map, unsafe, helpers, release, mode, unit, tests, shipped, matrix, checker, reports, undefined, behavior, integration, seeds, building, public, surface, reference, prose, exported, types, function, signatures, implementation, seed, audit, report, schema, version, workload, label, hash, clean, scenario, results, pass, count, total, floors, token]
```
