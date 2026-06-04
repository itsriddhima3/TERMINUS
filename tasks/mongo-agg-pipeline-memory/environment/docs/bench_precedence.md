# Bench precedence

When field bulletins, archived spill drafts, rollup policy chapters, and invoke lane contracts disagree, apply this order:

1. `/app/docs/rollup_policy/` — authoritative batch rollup semantics for WK lanes.
2. `/app/docs/invoke_lane_contract.md` — how batch invoke defaults merge with per-call options.
3. `/app/docs/spine_predicate_registry.md` — predicate groups per collection.
4. `/app/data/workload_matrix.json` — graded acceptance bands for the audit report.
5. `/app/docs/operations_notes.md` — shift bulletin; defers to rollup policy for spine ordering.
6. `/app/docs/archive/` — non-authoritative archaeology only.

Live spine code is wired from the runner under `/app/runners/` into bundle modules outside the reference tree under `/app/pipelines/`. Reference copies under `/app/pipelines/` are not on the live WK-SPINE path.
