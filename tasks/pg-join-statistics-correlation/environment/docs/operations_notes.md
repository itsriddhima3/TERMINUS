# Logistics planner operations

The fulfillment database lives in `logistics_db`. Schema bundles are under
`/app/store`. Workload definitions are under `/app/q`. Internal planner
reference chapters are under `/app/docs/planner_internals/`. Predicate groups
for spine replanning are listed in `/app/docs/correlation_registry.md`.

The audit harness executes the fifteen-table spine workload and writes
`/app/output/plan_audit.json`. Planner catalog changes should run through
`/app/lib/psql_wrap.sh` against `logistics_db`.
