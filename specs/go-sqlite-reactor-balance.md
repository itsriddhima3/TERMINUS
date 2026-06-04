### Decision
GO — Attempt 1. Milestone-scaffolded Go/SQLite facility CLI with cross-layer bootstrap, relational move gates, and session/playthrough invariants; opaque fix symbols across three package roots; twenty-four verifier tests split by milestone with flipping-point coverage.

### Metadata
- version: 2
- Task name: go-sqlite-reactor-balance
- Title: SQLite Reactor Balance
- Category: games
- Languages: ["go", "bash", "sql"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context", "tool_specific"]
- Tags: ["go", "sqlite", "cli", "puzzle", "interactive"]
- Milestones: 3

## Authoring Brief

### Public contract
Operators run `/app/bin/fluxctl` against a local SQLite catalog under `/app/var/game.db`. Milestone 1: `fluxctl init --scenario SCN-Alpha` must create the full relational catalog (chambers, components, constraints, rules, scenarios, sessions) and load SCN-Alpha seed rows from `/app/data/seeds/` so `fluxctl status --json` reports the opening metric triple and a populated 3×3 slot grid. Milestone 2: `fluxctl set <row> <col> <level>` must reject illegal adjustments using precedence-ordered rows in the rules table (adjacency delta caps, per-type level bounds, corner caps) before persisting; valid sets update levels and leave metrics unchanged until `fluxctl tick`. Milestone 3: repeated `tick` advances simulation; win when all three metrics sit inside documented bands for the scenario's required stable streak; loss on breach thresholds; `fluxctl save <slot>` / `fluxctl load <slot>` restore tick count, metrics, levels, and stable streak; `fluxctl run <script>` executes deterministic command transcripts for verification. Conflicting notes under `/app/docs/` — `/app/docs/bench_precedence.md` wins over `/app/docs/archive/`.

### Failure topology
Symptoms cluster in three layers. Bootstrap reports success but catalog queries show empty slot grids, missing constraint rows, or schema version markers that disagree with the precedence doc. Move acceptance ignores precedence-ordered relational gates — illegal adjacent level jumps or corner overshoots persist. Playthrough reaches in-band metrics yet never declares victory, resumes after save drop stable streak or tick index, or declares loss one tick late. The codebase presents as a conventional Go+SQLite CLI with decoy policy readers and grid helpers; the real defects sit in catalog materialization, rule evaluation order/joins, and outcome/session persistence coupling.

### Environment shape
Dockerized Go module at `/app`: `fluxctl` entrypoint, opaque packages `k9m` (catalog bootstrap), `r2n` (move gates), `w7p` (outcome/session), `m4t` (tick simulation), `p1v` (store), decoy modules, seed TOML, transcript scripts, precedence docs, bash build/probe helpers. Milestone tests invoke CLI subprocesses and inspect JSON status plus on-disk SQLite rows.

### Required artifacts
Milestone layout: `task.toml` with three `[[steps]]`, shared `environment/` (20+ files), `steps/milestone_N/{instruction.md, tests/{test.sh, test_mN.py}, solution/{solve.sh, solveN.sh, patches/}}`.

### Test plan
Milestone 1 (9 tests): catalog tables exist; SCN-Alpha nine slots; constraint rows for three component kinds; opening metric triple matches seed; schema version marker 2; repeat init idempotent; component levels seeded non-zero; catalog fingerprint stable across reruns; rule priority catalog and scenario loss/band fields.
Milestone 2 (10 tests): reject adjacent same-type delta>1; accept legal set; enforce max level from constraints; reject corner level 3; honor priority ordering when rules conflict; illegal set leaves DB unchanged; tick after legal set changes metrics; transcript illegal move exits non-zero; delta exactly 1 boundary accept; rod chain legal then block.
Milestone 3 (10 tests): winning transcript exits zero with victory flag; stable streak requires three ticks; save/load preserves tick and streak; loss on heat breach; resume continues win path; status JSON fields complete; run script deterministic hash; partial progress save restores levels; no victory before stable_needed; streak reset after metric drift.

### Drafting guardrails
Instructions stay symptoms-only per milestone: no SQL table lists, no fix-path package names, no numeric band literals beyond what docs name for verification scenarios, no oracle command sequences. Fix-path symbols opaque (`op_init`, `phase_v4`, `step_h3`). Code symbols must not echo instruction nouns. Decoy modules perform genuine ancillary reads.

### Triviality Ledger

- Creating tables without seed inserts passes table-existence checks but fails grid population and opening metric tests.
- Seeding components without level column mapping passes row counts but fails non-zero level and playthrough tests.
- Validating only max_level without adjacency or corner rules passes constraint tests but fails delta and corner rejection tests.
- Correct rule checks without priority ordering passes simple rejects but fails ordering trap where lower-priority rule would incorrectly allow move.
- Incrementing stable streak on set instead of tick passes single-tick win trap but fails three-tick streak requirement.
- Save without stable_streak passes metric restore but fails resume-win transcript test.
- Fixing outcome without save/load coupling passes fresh win transcript but fails mid-game save resume path.

### Hard calibration (≤20% target)

**Deep domain expertise:** Org-specific catalog memos (`/app/docs/catalog/`) reframe standard adjacency/corner/max gates as edge-kind coupling, corner envelope, and kind ceiling with bespoke strict-inequality coupling (`delta > param_a` rejects; equality permitted at band width 1). Dwell counter vs band ceiling vs breach cutoff (`loss_*`) are distinct columns easy to conflate.

**Complex multi-step reasoning (10+ steps):** Typical repair path spans bench precedence → catalog INDEX → memos 01–04 → worked examples → seed TOML cross-check → trace `op_init` / `phase_v4` / `step_h3` and save/load helpers → reject decoy orderings (`q3l`, `hub/r5v`) and `/app/docs/operations_notes.md` misdirects (REINDEX, WAL pragmas).

**Subtle debugging:** Bootstrap creates tables but skips constraint/rules seeding; revision marker B1 vs B2; level binding uses row ordinal; move path lacks `ORDER BY priority`, skips corner gate, inverts adjacency comparator; outcome uses band_hi for loss and streak≥1 for win; save zeros dwell counter and may lock SQLite without level buffering.

**Niche stack:** Go + CGO SQLite + ranked relational gates + session archive with `slot_levels` snapshot table.

**Disclosure control:** Milestone instructions are symptoms-only; fix checklist removed from `bench_precedence.md`. Authoritative semantics live in scattered catalog memos; archive and operations bulletin provide plausible wrong fixes.

**Verifier depth:** 29 tests (M1: 9, M2: 10, M3: 10) including boundary delta=1 accept, rod chain illegal tail, no victory before `stable_needed`, streak reset on drift, rule priority catalog fingerprint.

### Per-gate Pitfall Inventory

- RC1 — Oracle patches touch bootstrap, move gate, and outcome/session modules; not a one-file revert.
- RC6 — Milestone instructions describe observable drift, not DDL or fix sites.
- RC7 — Combined solve scripts ≥40 LOC substantive Go edits.
- CR2 — Flipping contract splits k9m, r2n, w7p across 8+8+8 tests (max ratio 8/24).
- CR7 — Instruction nouns banned from fix-path identifiers (`reactor`, `heat`, `pressure`, `flux`, etc.).
- GX9 — Expected SCN-Alpha opening metrics and win bands grounded in milestone instructions/docs before tests assert them.
- Static checks — Milestone `test_mN.py` classes, per-step `test.sh`, no root-level instruction/tests/solution.

### Initial Draft Commitments

- `tasks/go-sqlite-reactor-balance/task.toml`
- `tasks/go-sqlite-reactor-balance/environment/Dockerfile`
- `tasks/go-sqlite-reactor-balance/environment/go.mod`
- `tasks/go-sqlite-reactor-balance/environment/go.sum`
- `tasks/go-sqlite-reactor-balance/environment/.dockerignore`
- `tasks/go-sqlite-reactor-balance/environment/cmd/fluxctl/main.go`
- `tasks/go-sqlite-reactor-balance/environment/core/k9m/schema.go`
- `tasks/go-sqlite-reactor-balance/environment/core/r2n/check.go`
- `tasks/go-sqlite-reactor-balance/environment/core/w7p/outcome.go`
- `tasks/go-sqlite-reactor-balance/environment/core/m4t/sim.go`
- `tasks/go-sqlite-reactor-balance/environment/core/p1v/store.go`
- `tasks/go-sqlite-reactor-balance/environment/core/t2x/runscript.go`
- `tasks/go-sqlite-reactor-balance/environment/decoy/q3l/policy.go`
- `tasks/go-sqlite-reactor-balance/environment/decoy/n8f/gridread.go`
- `tasks/go-sqlite-reactor-balance/environment/lib/run_go.sh`
- `tasks/go-sqlite-reactor-balance/environment/scripts/build.sh`
- `tasks/go-sqlite-reactor-balance/environment/scripts/init_workspace.sh`
- `tasks/go-sqlite-reactor-balance/environment/app/probe_status.sh`
- `tasks/go-sqlite-reactor-balance/environment/data/seeds/SCN-Alpha.toml`
- `tasks/go-sqlite-reactor-balance/environment/data/seeds/SCN-Beta.toml`
- `tasks/go-sqlite-reactor-balance/environment/data/transcripts/win_alpha.script`
- `tasks/go-sqlite-reactor-balance/environment/data/transcripts/illegal_adj.script`
- `tasks/go-sqlite-reactor-balance/environment/docs/storage_contract.md`
- `tasks/go-sqlite-reactor-balance/environment/docs/seed_precedence.md`
- `tasks/go-sqlite-reactor-balance/environment/docs/move_policy.md`
- `tasks/go-sqlite-reactor-balance/environment/docs/win_conditions.md`
- `tasks/go-sqlite-reactor-balance/environment/docs/bench_precedence.md`
- `tasks/go-sqlite-reactor-balance/environment/docs/archive/legacy_storage.md`
- `tasks/go-sqlite-reactor-balance/environment/config/runtime.toml`
- `tasks/go-sqlite-reactor-balance/environment/platform/verifier-requirements.txt`
- `tasks/go-sqlite-reactor-balance/environment/platform/runtime.json`
- `tasks/go-sqlite-reactor-balance/steps/milestone_1/instruction.md`
- `tasks/go-sqlite-reactor-balance/steps/milestone_1/tests/test.sh`
- `tasks/go-sqlite-reactor-balance/steps/milestone_1/tests/test_m1.py`
- `tasks/go-sqlite-reactor-balance/steps/milestone_1/solution/solve.sh`
- `tasks/go-sqlite-reactor-balance/steps/milestone_1/solution/solve1.sh`
- `tasks/go-sqlite-reactor-balance/steps/milestone_1/solution/patches/m1_schema.patch`
- `tasks/go-sqlite-reactor-balance/steps/milestone_2/instruction.md`
- `tasks/go-sqlite-reactor-balance/steps/milestone_2/tests/test.sh`
- `tasks/go-sqlite-reactor-balance/steps/milestone_2/tests/test_m2.py`
- `tasks/go-sqlite-reactor-balance/steps/milestone_2/solution/solve.sh`
- `tasks/go-sqlite-reactor-balance/steps/milestone_2/solution/solve2.sh`
- `tasks/go-sqlite-reactor-balance/steps/milestone_2/solution/patches/m2_check.patch`
- `tasks/go-sqlite-reactor-balance/steps/milestone_3/instruction.md`
- `tasks/go-sqlite-reactor-balance/steps/milestone_3/tests/test.sh`
- `tasks/go-sqlite-reactor-balance/steps/milestone_3/tests/test_m3.py`
- `tasks/go-sqlite-reactor-balance/steps/milestone_3/solution/solve.sh`
- `tasks/go-sqlite-reactor-balance/steps/milestone_3/solution/solve3.sh`
- `tasks/go-sqlite-reactor-balance/steps/milestone_3/solution/patches/m3_outcome.patch`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/core/k9m/schema.go
  symbol: op_init
  kind: function
  signature: func op_init(db *sql.DB, sid string, seedRoot string) error
  purpose: Creates catalog tables, writes version marker, loads seed rows into chambers/components/constraints/rules/scenarios.

- path: environment/core/r2n/check.go
  symbol: phase_v4
  kind: function
  signature: func phase_v4(db *sql.DB, sid string, r, c, lvl int) error
  purpose: Evaluates precedence-ordered rule rows before accepting a level change at grid coordinates.

- path: environment/core/w7p/outcome.go
  symbol: step_h3
  kind: function
  signature: func step_h3(db *sql.DB, sid string, a, b, c int, streak int) (newStreak int, won bool, lost bool)
  purpose: Updates stable streak after tick metrics, evaluates win/loss bands, persists session fields on save/load helpers.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/core/k9m/schema.go
    controls_tests: [test_m1_catalog_tables, test_m1_alpha_nine_slots, test_m1_limit_rows_three, test_m1_open_triple_seed, test_m1_version_marker_two, test_m1_repeat_init_idempotent, test_m1_levels_nonzero, test_m1_catalog_fingerprint]
  - id: B
    path: environment/core/r2n/check.go
    controls_tests: [test_m2_reject_adjacent_delta, test_m2_accept_legal_set, test_m2_enforce_type_max, test_m2_reject_corner_three, test_m2_priority_order_trap, test_m2_illegal_unchanged_db, test_m2_tick_moves_metrics, test_m2_script_illegal_exit]
  - id: C
    path: environment/core/w7p/outcome.go
    controls_tests: [test_m3_win_script_zero, test_m3_stable_three_ticks, test_m3_save_load_streak, test_m3_loss_breach, test_m3_resume_win_path, test_m3_status_json_complete, test_m3_script_hash_stable, test_m3_mid_save_levels]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/decoy/q3l/policy.go
  kind: module
  rhymes_with: phase_v4
  non_fix_purpose: Reads archived policy TOML for display-only quota hints; never invoked on move path.

- path: environment/decoy/n8f/gridread.go
  kind: helper
  rhymes_with: op_init
  non_fix_purpose: Parses seed TOML into an in-memory preview grid for probe script without writing SQLite.

- path: environment/hub/r5v/gates.go
  kind: module
  rhymes_with: phase_v4
  non_fix_purpose: Display-only gate rank hints with wrong order and coupling band constant.

- path: environment/docs/operations_notes.md
  kind: doc
  rhymes_with: bench_precedence
  non_fix_purpose: Field bulletin misdirecting to SQLite pragmas and REINDEX instead of application fixes.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [facility, terminal, balancing, exercise, database, operators, fluxctl, init, puzzle, layouts, component, limits, scenario, seed, rows, seeds, installs, queries, chamber, grids, constraint, schema, versions, reference, notes, storage, precedence, bootstrap, relational, chambers, components, rules, scenarios, sessions, metrics, status, moves, validation, relational, win, loss, conditions, transcript, save, resume, player, game, state, commands, reactor, heat, pressure, neutron, flux, balance, sqlite, typed, scripted, playthrough]
```
