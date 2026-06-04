### Decision
GO — Attempt 1. MongoDB 7.0 telemetry rollup with spine aggregation memory failure; fixes span pipeline stage ordering, runner spill policy, and a trailing predicate stage; opaque symbols across pipelines, lib runner, and bash harness; twelve verifier tests with flipping-point coverage.

### Metadata
- version: 2
- Task name: mongo-agg-pipeline-memory
- Title: Mongo Spine Rollup
- Category: data-processing
- Languages: ["javascript", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["db_interaction", "tool_specific"]
- Tags: ["mongodb", "aggregation", "mongosh", "javascript", "performance"]
- Milestones: 0

## Authoring Brief

### Public contract
Operators repair the nightly spine rollup on MongoDB 7.0 against `telemetry_db`. The spine job aborts with memory limit exceeded during wide grouping on the events store. Production scale is on the order of fifty million documents; the lab replica is smaller but reproduces the same failure mode on the spine workload label `WK-SPINE-EMEA`.

Pipeline definitions live under `/app/pipelines/`. Run the spine job via `/app/runners/k7_execute.sh`. The graded harness is `/app/app/pipeline_audit.sh`, which writes `/app/output/pipeline_audit.json`. Acceptance bands are in `/app/data/workload_matrix.json`. Predicate groups for the spine workload are in `/app/docs/spine_predicate_registry.md`. Use `/app/lib/mongosh_wrap.sh` for analyst-role database access.

The audit JSON carries schema_version, workload_label, spine_collection, filter_region, filter_event_type, result_total, grouped_keys, memory_limit_exceeded, allow_disk_enabled, first_stage_kind, match_stage_index, examined_to_returned_ratio, and pipeline_hash.

### Failure topology (hard calibration)
Four independent defects must be found and fixed; no single edit flips a majority of tests (flipping-point cap 50% across `x9/p9a_bundle.js`, `r7/h3v_invoke.js`, `m4/q2m_attach.js`, `config/invoke_policy.json`).

1. **Stage order** (`phase_bundle`): `$group` before selective `$match` on raw `region` / `event_type` — MongoDB 7.0 blocking-stage RAM blow-up on 120k lab events.
2. **Invoke policy + wrapper** (`spine_defaults` + `mergeOpts`): policy JSON disables spill; wrapper reads policy but hardcodes `allowDiskUse: false` — fixing only JSON is insufficient.
3. **Tail attachment** (`step_tail`): post-group `$match` on `cfg.event_type` (undefined; profile uses `eventType`) — empty spine totals despite “successful” runs.
4. **Discovery friction**: instruction points at `/app/pipelines/`; live path is `k7_execute.sh` → `n4_exec.js` → `x9`/`m4`/`r7`. Decoys: `p9_spine_mirror.js`, `p9b_legacy.js`, `hub/r7b_invoke.js`, `docs/archive/legacy_spill.md`. Authoritative ordering in `docs/rollup_policy/` via `docs/bench_precedence.md`.

**Expected agent path (12+ steps):** run failing lane → read audit JSON → compare workload_matrix bands → trace runner (not pipelines mirror) → read bench_precedence → rollup_policy ch.03–05 → fix bundle order → fix invoke policy → fix mergeOpts to honor policy → neutralize tail → rerun audit → confirm independent_total cross-check.

Symptoms cluster in memory-limit aborts, zero totals, and high examined ratios while decoy rollups on `metrics_snap` still succeed.

### Environment shape
Dockerized MongoDB 7.0 at `/app`: mongosh pipelines, bash runners, audit harness, seed generator, predicate registry docs, aggregation limit reference chapters, decoy rollup modules, config profiles, init/bootstrap scripts.

### Required artifacts
Standard layout: instruction.md, task.toml, output_contract.toml, environment/ (20+ files), solution/solve.sh, tests/{test.sh, test_outputs.py}.

### Test plan (26 tests)
- test_audit_report_exists_and_schema: report file with all contract fields
- test_spine_run_exit_zero: k7_execute.sh succeeds
- test_memory_limit_not_exceeded: memory_limit_exceeded is false
- test_allow_disk_enabled: allow_disk_enabled true per workload matrix
- test_first_stage_is_match: first_stage_kind is match
- test_match_stage_index_zero: match_stage_index is 0
- test_result_total_in_band: result_total within matrix band
- test_grouped_keys_in_band: grouped_keys within matrix band
- test_examined_ratio_below_cap: examined_to_returned_ratio at or below cap
- test_pipeline_hash_stable: pipeline_hash matches matrix expectation after fix
- test_rerun_idempotent: second audit matches first on key fields
- test_decoy_rollup_untouched: decoy collection rollup still passes matrix decoy band
- Hard-band: stage_digest, independent_total cross-check, selective examined ratio, triple-audit stability, invoke_policy spill, live runner wires x9 (not mirror), bench_precedence ordering

### Drafting guardrails
Instruction stays symptoms-only: no stage operator names as fix recipe, no allowDiskUse flag enumeration, no file-level fix map. Fix-path symbols opaque (phase_bundle, op_exec, step_tail). Code symbols must not echo instruction nouns. Decoy modules perform genuine ancillary rollups.

### Triviality Ledger

- Enabling spill alone passes memory test but fails first_stage_is_match and examined_ratio tests because grouping still scans the full store.
- Moving match first without removing the tail predicate passes ratio tests but fails pipeline_hash and result_total bands because the tail stage zeroes valid groups.
- Reordering only the decoy pipeline passes decoy test but spine runner still fails memory_limit_exceeded.
- Hardcoding audit JSON passes schema test but fails rerun idempotency and pipeline_hash checks tied to live explain output.

### Per-gate Pitfall Inventory

- RC1 — Oracle edits pipeline stages, runner aggregate options, and tail module; not a one-line revert.
- RC6 — Instruction describes abort symptoms and report contract, not operator reorder recipes.
- RC7 — Combined solve.sh substantive edits across JS and bash ≥40 LOC.
- CR2 — Flipping contract splits wk_spine.js, m4t_runner.js, lane_tail.js across four/four/four tests.
- CR7 — Instruction nouns banned from fix-path identifiers.
- GX9 — WK-SPINE-EMEA bands and filter tokens grounded in instruction and workload_matrix before tests assert them.
- RC3 — Tests assert computed totals and explain ratios, not existence-only.

### Initial Draft Commitments

- tasks/mongo-agg-pipeline-memory/task.toml
- tasks/mongo-agg-pipeline-memory/output_contract.toml
- tasks/mongo-agg-pipeline-memory/instruction.md
- tasks/mongo-agg-pipeline-memory/environment/Dockerfile
- tasks/mongo-agg-pipeline-memory/environment/.dockerignore
- tasks/mongo-agg-pipeline-memory/environment/init/docker-entrypoint-wrapper.sh
- tasks/mongo-agg-pipeline-memory/environment/init/ensure_mongo.sh
- tasks/mongo-agg-pipeline-memory/environment/init/bootstrap.sh
- tasks/mongo-agg-pipeline-memory/environment/init/post_boot.sh
- tasks/mongo-agg-pipeline-memory/environment/app/pipeline_audit.sh
- tasks/mongo-agg-pipeline-memory/environment/lib/mongosh_wrap.sh
- tasks/mongo-agg-pipeline-memory/environment/lib/m4t_runner.js
- tasks/mongo-agg-pipeline-memory/environment/pipelines/wk_spine.js
- tasks/mongo-agg-pipeline-memory/environment/pipelines/lane_tail.js
- tasks/mongo-agg-pipeline-memory/environment/pipelines/decoy_beta.js
- tasks/mongo-agg-pipeline-memory/environment/runners/k7_execute.sh
- tasks/mongo-agg-pipeline-memory/environment/config/runtime.toml
- tasks/mongo-agg-pipeline-memory/environment/config/spine_profile.json
- tasks/mongo-agg-pipeline-memory/environment/data/workload_matrix.json
- tasks/mongo-agg-pipeline-memory/environment/docs/spine_predicate_registry.md
- tasks/mongo-agg-pipeline-memory/environment/docs/operations_notes.md
- tasks/mongo-agg-pipeline-memory/environment/docs/aggregation_limits/INDEX.md
- tasks/mongo-agg-pipeline-memory/environment/docs/aggregation_limits/chapter_01.md
- tasks/mongo-agg-pipeline-memory/environment/docs/aggregation_limits/chapter_02.md
- tasks/mongo-agg-pipeline-memory/environment/tools/gen_seed.py
- tasks/mongo-agg-pipeline-memory/environment/store/001_collections.js
- tasks/mongo-agg-pipeline-memory/environment/store/002_indexes.js
- tasks/mongo-agg-pipeline-memory/environment/migrations/v1_note.js
- tasks/mongo-agg-pipeline-memory/environment/migrations/x9_decoy.js
- tasks/mongo-agg-pipeline-memory/environment/decoy/q3l_rollup.js
- tasks/mongo-agg-pipeline-memory/environment/decoy/n8f_preview.js
- tasks/mongo-agg-pipeline-memory/environment/hub/r5v_stages.js
- tasks/mongo-agg-pipeline-memory/environment/platform/runtime.json
- tasks/mongo-agg-pipeline-memory/environment/platform/verifier-requirements.txt
- tasks/mongo-agg-pipeline-memory/solution/solve.sh
- tasks/mongo-agg-pipeline-memory/tests/test.sh
- tasks/mongo-agg-pipeline-memory/tests/test_outputs.py

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/pipelines/wk_spine.js
  symbol: phase_bundle
  kind: function
  signature: function phase_bundle(cfg) { return Array; }
  purpose: Builds ordered aggregation stage array for spine workload from profile config.

- path: environment/lib/m4t_runner.js
  symbol: op_exec
  kind: function
  signature: function op_exec(db, coll, stages, opts) { return cursor; }
  purpose: Invokes aggregate on collection with caller options object.

- path: environment/pipelines/lane_tail.js
  symbol: step_tail
  kind: function
  signature: function step_tail(stages, cfg) { return Array; }
  purpose: Appends trailing predicate stages to supplied stage array.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/pipelines/wk_spine.js
    controls_tests: [test_first_stage_is_match, test_match_stage_index_zero, test_examined_ratio_below_cap, test_pipeline_hash_stable]
  - id: B
    path: environment/lib/m4t_runner.js
    controls_tests: [test_memory_limit_not_exceeded, test_allow_disk_enabled, test_spine_run_exit_zero]
  - id: C
    path: environment/pipelines/lane_tail.js
    controls_tests: [test_result_total_in_band, test_grouped_keys_in_band, test_rerun_idempotent, test_decoy_rollup_untouched]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/decoy/q3l_rollup.js
  kind: module
  rhymes_with: phase_bundle
  non_fix_purpose: Hourly beta rollup on metrics_snap collection for dashboard previews.

- path: environment/decoy/n8f_preview.js
  kind: helper
  rhymes_with: op_exec
  non_fix_purpose: Read-only explain preview without writing audit output.

- path: environment/hub/r5v_stages.js
  kind: module
  rhymes_with: step_tail
  non_fix_purpose: Static stage label map for documentation tooling only.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [telemetry, rollup, mongodb, memory, limit, exceeded, spine, aggregation, events, store, pipelines, audit, harness, output, workload, matrix, predicate, registry, analyst, repair, report, schema, operators, nightly, aborts, grouping, production, replica, failure, definitions, runners, bands, groups, filters, access, collection, region, purchase, totals, keys, disk, enabled, stage, index, examined, returned, ratio, hash, decoy, mongosh, javascript, bash, performance, data, processing]
```
