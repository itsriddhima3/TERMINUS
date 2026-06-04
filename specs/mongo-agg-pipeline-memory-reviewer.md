### Decision
GO — Attempt 1.

### Metadata
- Task name: mongo-agg-pipeline-memory
- Title: Mongo Spine Rollup
- Category: data-processing
- Difficulty: hard

### Discovery budget
- Discovery: Spine runner omits disk spill on aggregate invocation despite batch policy docs.
  Planned location: environment/lib/m4t_runner.js
  Why instruction must not reveal it: Would reduce diagnosis to flag transcription.
- Discovery: Grouping precedes raw-field predicates in phase_bundle ordering.
  Planned location: environment/pipelines/wk_spine.js
  Why instruction must not reveal it: Names the exact stage reorder recipe.
- Discovery: step_tail appends a predicate on document fields after grouping nullifies groups.
  Planned location: environment/pipelines/lane_tail.js
  Why instruction must not reveal it: Points to single trailing file edit.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch: Reorder match ahead of group/sort, enable allowDiskUse in op_exec, strip tail match from step_tail.

Likely editable frontier: pipelines/wk_spine.js, pipelines/lane_tail.js, lib/m4t_runner.js, runners/k7_execute.sh (read-only invoke).

Collapse verdict: PASS
