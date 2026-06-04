### Decision
GO — Attempt 1. Redis 7.2 split round-trip hold pipeline with stale baseline ARGV, alias key routing, and twelve-scenario audit harness.

### Metadata
- Task name: redis-lua-hold-reconcile
- Title: Redis Hold Reconcile
- Category: debugging
- Languages: ["lua", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["db_interaction", "tool_specific"]
- Tags: ["redis", "lua", "concurrency", "bash", "inventory"]
- Milestones: 0

### Discovery budget
- Discovery: Host-side GET passes a frozen baseline snapshot into the commit Lua body via ARGV, so parallel workers commit against stale counts even though each EVAL is individually atomic.
  Planned location: `environment/worker/phase_r8.sh` + `environment/lua/op_n2.lua`
  Why instruction must not reveal it: Naming the round-trip split collapses diagnosis to a textbook Redis atomicity FAQ.

- Discovery: Worker routing resolves catalog labels to `hold:*` alias keys while the seed catalog loads canonical `sku:*` keys — burst lanes can appear healthy on canonical keys while alias lanes overshoot.
  Planned location: `environment/lib/k7m/step_w1.sh` + `environment/lib/seed_helpers.sh`
  Why instruction must not reveal it: Instruction only names symptoms (overshoot under parallelism), not key topology.

- Discovery: Operations notes recommend backoff and MULTI/EXEC wrapping — partial mitigations that pass solo lanes but leave burst/retry scenarios overshooting.
  Planned location: `environment/docs/operations_notes.md`
  Why instruction must not reveal it: Cause-revealing ops guidance would steer agents away from reading dispatch/Lua coupling.

### Collapse audit
Stage: post-build

Smallest plausible successful patch: Collapse host pre-read and commit into one EVAL; teach Lua body to DECRBY internally without ARGV baseline; map labels through sku_catalog.json canonical keys.

Oracle estimated complexity: ~37 LOC substantive edit across worker, Lua, router.

Collapse verdict: WARN (borderline oracle LOC, GX9 at 50% saturation)

### Naming-pass record

**Instruction nouns extracted:**
warehouse, hold, service, reservation, requests, catalog, SKUs, Alpha-Unit, Beta-Crate, Gamma-Tote, operators, stock_audit, report, schema_version, catalog_skus, scenarios, stock_compliance, stress_summary, oversell_detected, total_granted, final_stock, requests_attempted, parallel, workers, units, opening, count, grading

**Renames during drafting:**
- baseline.marker → epoch_v1.tag (RC5 reference-artifact pattern)

**Test names audited:**
- test_report_schema_version through test_stress_summary_clean (no instruction noun substrings)

**Concentration math:**
- Total tests: 13
- worker/phase_r8.sh: 5/13 = 38%
- lua/op_n2.lua: 4/13 = 31%
- lib/k7m/step_w1.sh: 3/13 = 23%
- Cap: 0.5. Max ratio: 38%. Status: PASS
