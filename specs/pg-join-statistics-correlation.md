### Decision
GO — Attempt 1. Long-context PostgreSQL planner statistics task with correlated column mis-estimation driving nested-loop plans.

### Metadata
- version: 2
- Task name: pg-join-statistics-correlation
- Title: Join Statistics Correlation
- Category: scientific-computing
- Languages: ["bash", "sql"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context", "db_interaction"]
- Tags: ["postgresql", "query-planning", "statistics", "sql", "performance"]
- Milestones: 0

## Authoring Brief

### Public contract
Agent receives PostgreSQL 15 logistics schema with fifteen-table spine query, ~119k-word planner internals corpus under `/app/docs/planner_internals/`, and `/app/app/plan_audit.sh` writing `/app/output/plan_audit.json`. Broken state uses nested loops with bridge estimate ratio far from band; repair via extended statistics, statistics targets, and ANALYZE per Section 7.3 in chapter_07_statistics.md.

### Failure topology
Correlated region_id and zone_code filters on bridge_facility_zone cause independent selectivity product; planner underestimates join cardinality and prefers nested loops on the wide spine.

### Environment shape
Dockerized PostgreSQL 15, SQL schema/seed bundles, opaque stats SQL fragments across store/, migrations/, lib/, bash audit harness, long-form docs corpus.

### Required artifacts
Standard single-step layout with 40+ environment files including generated docs and seed SQL.

### Test plan
Ten tests reading acceptance bands from workload_matrix.json covering schema contract, filter constants, hash joins, spine driver, bridge ratio, nested loop cap, result total band.

### Triviality Ledger
- Raising statistics targets alone may fix ratio but not hash join count without extended stats objects.
- ANALYZE without dependency statistics leaves bridge ratio inflated.
- Disabling nested loops via GUC would pass join counts but fails domain-specific ratio tests.

### Per-gate Pitfall Inventory
- RC6: instruction lists field names only; values live in workload_matrix.json.
- CR2: fix paths split across store/, migrations/, lib/ roots.
- GX9: no numeric answer recital in instruction prose.

### Initial Draft Commitments
- tasks/pg-join-statistics-correlation/** (full task tree)
