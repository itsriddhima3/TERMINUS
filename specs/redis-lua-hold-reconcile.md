### Decision
GO — Attempt 1. Redis 7.2 concurrent hold pipeline with split round-trip orchestration, opaque fix symbols across worker dispatch, Lua commit body, and catalog key routing; twelve scenario rows blocking naive mutex/pipeline/MULTI-only shortcuts.

### Metadata
- version: 2
- Task name: redis-lua-hold-reconcile
- Title: Redis Hold Reconcile
- Category: debugging
- Languages: ["lua", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["db_interaction", "tool_specific"]
- Tags: ["redis", "lua", "concurrency", "bash", "inventory"]
- Milestones: 0

## Authoring Brief

### Public contract
Operators run a Redis 7.2 warehouse hold service for three catalog SKUs — Alpha-Unit (six units), Beta-Crate (ten), Gamma-Tote (four). `/app/app/stock_audit.sh` writes `/app/output/stock_audit.json` with `schema_version` 1, `catalog_skus`, a `scenarios` map, and `stock_compliance` flags. Each scenario row reports `oversell_detected`, `total_granted`, `final_stock`, and `requests_attempted`. Parallel worker lanes occasionally grant more units than the SKU cap while single-lane replays look clean. Agent must repair the hold pipeline so every scenario reports `oversell_detected: false`, `final_stock` never negative, and `total_granted` never exceeds the scenario's starting cap. Grading reads `/app/output/stock_audit.json`.

### Failure topology
Symptoms cluster under parallel reservation workers: granted totals exceed starting stock while sequential audit lanes pass. The codebase presents as a conventional Redis+Lua hold stack — catalog JSON, worker dispatch shell, Lua commit bodies, metrics decoys — but embeds a split round-trip pattern between a host-side stock read and a separate script invocation. A companion Lua body uses read-modify-write internally yet remains safe only when invoked alone; the orchestrator reintroduces a network gap. Catalog key routing uses a lowercase alias table that diverges from seed keys for two SKUs under burst load. Operations notes misdirect toward client-side retry/backoff rather than atomicity boundaries.

### Environment shape
Dockerized Redis 7.2 tree under `/app`: init/bootstrap helpers, Lua scripts in `/app/lua/`, worker dispatch under `/app/worker/`, opaque routing helper under `/app/lib/k7m/`, bash scenario drivers, SKU catalog JSON, worker policy TOML, hold pipeline doc, decoy metrics/flush modules. Tests invoke the stock audit harness against live Redis state.

### Required artifacts
Standard single-step layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (20+ files), `solution/solve.sh`, `tests/test.sh`, `tests/test_outputs.py`.

### Test plan
- `test_report_schema_version` — schema_version equals 1
- `test_catalog_skus_present` — three SKU labels in order
- `test_all_scenarios_present` — twelve scenario keys exist
- `test_solo_lane_clean` — single worker on Alpha-Unit grants 3, no oversell
- `test_burst_dual_no_oversell` — two parallel workers on Alpha-Unit cap at 6 granted
- `test_burst_quad_no_oversell` — four workers on Beta-Crate cap at 10 granted
- `test_mixed_skus_isolated` — parallel Alpha + Gamma lanes do not cross-grant
- `test_zero_floor_honored` — exact depletion leaves final_stock 0 without oversell
- `test_pipe_burst_clean` — pipelined worker simulation stays within cap
- `test_retry_lane_clean` — retrying workers do not double-grant
- `test_reject_over_cap` — requests above stock return zero grant without negative stock
- `test_no_scenario_oversell` — all rows false on oversell_detected
- `test_stress_summary_clean` — stress block reports zero oversell events

### Drafting guardrails
Instruction stays symptoms-only: no EVAL/DECR/MULTI vocabulary, no orchestrator file paths, no round-trip count recipe. Fix-path symbols opaque (`op_n2`, `phase_r8`, `step_w1`). Code symbols must not echo instruction nouns. Decoy Lua/shell modules perform genuine ancillary reads. Operations notes recommend backoff — wrong root cause.

### Triviality Ledger

- Wrapping the existing Lua body in MULTI/EXEC from bash while keeping the host-side GET passes solo lane but fails burst_dual because the pre-check read sits outside the transaction.
- Fixing only the Lua GET/SET to DECRBY without collapsing orchestrator round trips passes sequential scenarios but fails pipe_burst when the host still reads stock before EVAL.
- Correcting key routing alone prevents wrong-key writes but fails burst_quad when split round trips remain on the canonical sku keys.
- Increasing worker sleep/backoff per operations notes reduces flake rate cosmetically but fails stress_summary under full parallel fan-out.
- Patching dispatch to call EVAL twice (probe then commit) atomically per call but still sequentially from bash fails retry_lane when workers interleave probe windows.

### Per-gate Pitfall Inventory

- RC1 — Oracle must rewrite orchestrator round trips, Lua commit atomicity, and catalog key routing; not a one-line timeout tweak.
- RC6 — Instruction must not name DECR, EVAL, MULTI, or worker script paths.
- RC7 — solve.sh includes substantive bash/Lua edits across three loci (≥40 LOC non-boilerplate).
- CR1/CR7 — Use committed symbol names `op_n2`, `phase_r8`, `step_w1`; no instruction nouns on fix path.
- CR2 — flipping_point_contract splits worker dispatch, Lua body, and key router across twelve tests (max ratio 5/12).
- GX9 — Ground Alpha-Unit 6, Beta-Crate 10, Gamma-Tote 4 opening caps in instruction before tests assert totals.
- Static checks — `db_interaction` + `tool_specific` subcategories; env file count ≥20.

### Initial Draft Commitments

- `tasks/redis-lua-hold-reconcile/instruction.md`
- `tasks/redis-lua-hold-reconcile/task.toml`
- `tasks/redis-lua-hold-reconcile/output_contract.toml`
- `tasks/redis-lua-hold-reconcile/environment/Dockerfile`
- `tasks/redis-lua-hold-reconcile/environment/.dockerignore`
- `tasks/redis-lua-hold-reconcile/environment/init/bootstrap_once.sh`
- `tasks/redis-lua-hold-reconcile/environment/init/docker-entrypoint-wrapper.sh`
- `tasks/redis-lua-hold-reconcile/environment/init/ensure_redis.sh`
- `tasks/redis-lua-hold-reconcile/environment/init/bootstrap.sh`
- `tasks/redis-lua-hold-reconcile/environment/init/post_boot.sh`
- `tasks/redis-lua-hold-reconcile/environment/lua/op_n2.lua`
- `tasks/redis-lua-hold-reconcile/environment/lua/q3l_probe.lua`
- `tasks/redis-lua-hold-reconcile/environment/worker/phase_r8.sh`
- `tasks/redis-lua-hold-reconcile/environment/lib/k7m/step_w1.sh`
- `tasks/redis-lua-hold-reconcile/environment/lib/redis_wrap.sh`
- `tasks/redis-lua-hold-reconcile/environment/lib/result_collect.sh`
- `tasks/redis-lua-hold-reconcile/environment/lib/json_merge.sh`
- `tasks/redis-lua-hold-reconcile/environment/app/stock_audit.sh`
- `tasks/redis-lua-hold-reconcile/environment/app/scenario_a.sh` through `scenario_l.sh`
- `tasks/redis-lua-hold-reconcile/environment/data/sku_catalog.json`
- `tasks/redis-lua-hold-reconcile/environment/data/scenario_matrix.json`
- `tasks/redis-lua-hold-reconcile/environment/config/redis.conf.snippet`
- `tasks/redis-lua-hold-reconcile/environment/config/worker_policy.toml`
- `tasks/redis-lua-hold-reconcile/environment/docs/operations_notes.md`
- `tasks/redis-lua-hold-reconcile/environment/docs/hold_pipeline.md`
- `tasks/redis-lua-hold-reconcile/environment/decoy/n8f_metrics.lua`
- `tasks/redis-lua-hold-reconcile/environment/decoy/p4x_flush.sh`
- `tasks/redis-lua-hold-reconcile/environment/migrations/baseline.marker`
- `tasks/redis-lua-hold-reconcile/solution/solve.sh`
- `tasks/redis-lua-hold-reconcile/tests/test.sh`
- `tasks/redis-lua-hold-reconcile/tests/test_outputs.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/worker/phase_r8.sh
  symbol: phase_r8
  kind: function
  signature: phase_r8() { local a=$1; local b=$2; ... }
  purpose: dispatches a hold attempt for catalog label and quantity through redis-cli

- path: environment/lua/op_n2.lua
  symbol: op_n2
  kind: function
  signature: -- KEYS[1] slot key, ARGV[1] quantity (Lua script body loaded by EVAL)
  purpose: applies quantity deduction against the resolved slot key

- path: environment/lib/k7m/step_w1.sh
  symbol: step_w1
  kind: function
  signature: step_w1() { local a=$1; ... }
  purpose: maps catalog label string to Redis key prefix used by workers
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/worker/phase_r8.sh
    controls_tests: [test_burst_dual_no_oversell, test_burst_quad_no_oversell, test_pipe_burst_clean, test_retry_lane_clean, test_stress_summary_clean]
  - id: B
    path: environment/lua/op_n2.lua
    controls_tests: [test_solo_lane_clean, test_zero_floor_honored, test_reject_over_cap, test_no_scenario_oversell]
  - id: C
    path: environment/lib/k7m/step_w1.sh
    controls_tests: [test_mixed_skus_isolated, test_catalog_skus_present, test_all_scenarios_present]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/lua/q3l_probe.lua
  kind: module
  rhymes_with: op_n2
  non_fix_purpose: read-only stock probe used by metrics sidecar; not on grant hot path when routing is correct

- path: environment/decoy/p4x_flush.sh
  kind: helper
  rhymes_with: phase_r8
  non_fix_purpose: periodic TTL sweep for ancillary cache keys

- path: environment/decoy/n8f_metrics.lua
  kind: module
  rhymes_with: op_n2
  non_fix_purpose: INCRBY counters for observability lanes
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [warehouse, hold, service, reservation, oversell, catalog, stock, pipeline, grant, workers, parallel, units, Alpha-Unit, Beta-Crate, Gamma-Tote, audit, scenario, compliance, lane, burst, retry, pipe, stress]
```
