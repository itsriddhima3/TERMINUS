### Decision
GO — Attempt 1. Milestone Go/SQLite reactor CLI with three fix loci; oracle 1.0 and NOP 0.0 verified.

### Metadata
- Task name: go-sqlite-reactor-balance
- Title: SQLite Reactor Balance
- Category: games
- Languages: ["go", "bash", "sql"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context", "tool_specific"]
- Tags: ["go", "sqlite", "cli", "puzzle", "interactive"]
- Milestones: 3

### Discovery budget
- Discovery: Relational gate rows are seeded via catalog bootstrap, not inferred from TOML `[[rules]]` alone when constraints map succeeds but rules slice decode is empty.
  Planned location: `environment/core/k9m/schema.go` hardcoded `catalogRules` insert loop
  Why instruction must not reveal it: Would collapse milestone 1 to reading one seed file.

- Discovery: Same-kind adjacency applies only to edge neighbors on the 3×3 grid; diagonal rods never trigger adjacency_delta.
  Planned location: `environment/data/seeds/SCN-Alpha.toml` layout + `environment/core/r2n/check.go` `checkAdjacency`
  Why instruction must not reveal it: Would let agents skip grid analysis and patch adjacency blindly.

- Discovery: SQLite rejects writes while a read cursor is open; save/load must buffer component rows before updating `slot_levels` / `components`.
  Planned location: `environment/core/w7p/outcome.go` SaveSlot/LoadSlot
  Why instruction must not reveal it: Symptom is opaque "database is locked" at runtime.

### Anti-trivialization verdict
Pass — cross-milestone coupling, relational precedence, session/grid persistence, and simulation bands interact; no single-line oracle.

### Rubric axes
All six axes Pass for games/debugging hybrid CLI task with deterministic transcripts.

### Hardness axes
Discover/Synthesize/Diagnose/Navigate coupling/Reason beyond training satisfied via bootstrap vs move-gate vs outcome layers and SQLite session semantics.

### Instruction completeness test
Fail instruction-only solve — agent must read env code, seed layout, and docs precedence to repair three modules.

## Reviewer Appendix

### Implementation plan
Broken `fluxctl` CLI under `/app` with SQLite catalog. Milestone 1 fixes `op_init` bootstrap; milestone 2 fixes `phase_v4` move gates; milestone 3 fixes `step_h3` outcome and save/load grid persistence.

### Proposed file inventory
See `specs/go-sqlite-reactor-balance.md` Initial Draft Commitments (30 environment files + 3 milestone steps).

### Oracle notes
Patches `m1_schema.patch`, `m2_check.patch`, `m3_outcome.patch` applied per milestone; rebuild via `/app/scripts/build.sh`.

### Collapse audit
Stage: post-build. Verdict: PASS with distributed fix across k9m/r2n/w7p.

### Naming-pass record
Instruction nouns extracted: facility, terminal, balancing, exercise, database, operators, fluxctl, init, puzzle, layouts, component, limits, scenario, seed, rows, seeds, queries, chamber, grids, constraint, schema, versions, reference, notes, storage, precedence, bootstrap, relational, chambers, components, rules, scenarios, sessions, metrics, status, moves, validation, win, loss, conditions, transcript, save, resume, player, game, state, commands, reactor, heat, pressure, neutron, flux, balance, sqlite, typed, scripted, playthrough

Test names audited: test_m1_catalog_tables, test_m2_reject_adjacent_delta, test_m3_win_script_zero, etc. — no instruction noun substrings.

Concentration math: 8/24 per location, cap 0.5, PASS.
