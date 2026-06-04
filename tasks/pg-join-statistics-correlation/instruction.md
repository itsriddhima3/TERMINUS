Our logistics PostgreSQL 15 database runs a fifteen-table fulfillment spine query in about forty-five seconds. Planner row estimates on correlated region and zone filters are far off observed counts, and the join plan stays probe-heavy on wide fact paths.

Planner reference chapters are under `/app/docs/planner_internals/`. Predicate groups for the spine workload are in `/app/docs/correlation_registry.md`. Acceptance bands for `/app/output/plan_audit.json` are in `/app/data/workload_matrix.json`.

Repair catalog statistics and replanning behavior on `logistics_db`, then run `/app/app/plan_audit.sh` to write the audit report. Use `/app/lib/psql_wrap.sh` for planner-role database access. The graded report must satisfy every acceptance band in the workload matrix.

The audit JSON carries schema_version, workload_label, catalog_tables, filter_region_id, filter_zone_code, result_total, spine_driver, bridge_estimate_ratio, inventory_estimate_ratio, plan_root_rows, actual_root_rows, and join_methods with nested_loop_count, hash_join_count, and merge_join_count.
