### Decision
GO — Attempt 1. PostgreSQL RLS plan-cache isolation task with distributed fix across q/x7q.sql, q/m2p.sql, and v/h3v.sql.

### Metadata
- Task name: rls-session-boundary-leak
- Title: RLS Session Boundary Leak
- Category: security
- Languages: ["bash", "sql"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["db_interaction"]
- Tags: ["postgresql", "rls", "multi-tenant", "sql", "isolation"]
- Milestones: 0

### Discovery budget
- Discovery: RLS policies inline `current_setting('app.scope_id')` which binds to generic prepared plans.
  Planned location: `environment/q/m2p.sql`
  Why instruction must not reveal it: naming plan-cache interaction collapses diagnosis to a web search.

- Discovery: `fn_k7()` exists as STABLE but is unused by policies — decoy partial fix path.
  Planned location: `environment/q/x7q.sql`
  Why instruction must not reveal it: wiring STABLE accessor alone looks sufficient but fails reuse scenarios.

- Discovery: `svc_runner` role lacks `plan_cache_mode = force_custom_plan` while scenarios force generic plans.
  Planned location: `environment/v/h3v.sql`
  Why instruction must not reveal it: stating the knob name turns the task into config transcription.

### Anti-trivialization verdict
Passes discovery budget (3+), topology distribution (function + policies + role), and symptoms-only instruction. Security aura discounted — residual work is PostgreSQL planner/RLS coupling, not CVE trivia.

### Topology enumeration (3 candidate fix topologies)
1. Policy-only rebind to accessor — fails reuse_stmt/pool_rotate without volatility/plan mode.
2. Role plan_cache_mode only — ad-hoc paths improve but join/view paths still leak with inlined settings in policies.
3. Full fix: VOLATILE accessor + policy rebind + force_custom_plan — only topology passing all six scenarios.

### Rubric axes
All six pass: deterministic JSON audit, well-specified report contract, expert-solvable in hours, hard due to PG planner semantics, real multi-tenant ops value, outcome-verified via boundary_audit.json.

### Hardness axes
Discover (read q/m2p, v/h3v, scenario scripts), Synthesize (RLS + prepared statements + role GUCs), Diagnose (symptoms-only instruction), Navigate coupling (policy + function + role), Reason beyond training (generic plan + RLS interaction).

### Instruction completeness test
Cannot solve from instruction alone — must run audit scenarios and inspect SQL bundles under `/app/q` and `/app/v`.

## Reviewer Appendix

### Implementation plan
Single-container PostgreSQL 15 image with seeded multi-org schema, broken RLS using inlined session reads, audit matrix simulating pooled/prepared access with `force_generic_plan`. Oracle rewrites three SQL bundles and adds trigger helper.

### Proposed file inventory
38 files under `environment/` across `store/`, `q/`, `v/`, `app/`, `lib/`, `data/`, `views/`, `migrations/`, `init/`, `config/`, `docs/`.

### Oracle notes
`solve.sh` heredoc-writes corrected `q/x7q.sql`, `q/m2p.sql`, `v/h3v.sql`, creates `q/n4w.sql`, applies via psql, runs audit_runner.

### Collapse audit
Stage: post-construction

Smallest plausible successful patch: change STABLE→VOLATILE, swap policy expressions to fn_k7(), add force_custom_plan — but must discover all three loci from failing scenarios.

Likely editable frontier: q/x7q.sql, q/m2p.sql, v/h3v.sql

Collapse verdict: PASS (WARN on RC6 schema density, RC8 gate concentration, CR1 SQL symbol extraction limit)

### Naming-pass record
**Instruction nouns extracted:** postgresql, backend, row, filters, catalog, organization, ledger, rows, acme-crate, beta-tote, delta-bin, audit, runner, boundary, json, schema, version, labels, scenarios, cross_scope_visible, foreign_labels_seen, owned_row_count, patterns, context, connection, grading

**Renames during drafting:** gate/→q/, profiles/→v/, scope_reader→x7q.sql, policies→m2p.sql, app_role→h3v.sql

**Test names audited:** test_report_schema_version, test_catalog_labels_present, test_all_scenarios_present, test_no_scenario_leaks, test_adhoc_single_row_count, test_reuse_stmt_row_count, test_pool_rotate_row_count, test_join_path_row_count, test_view_path_row_count, test_batch_fetch_row_count, test_foreign_labels_are_strings

**Concentration math:**
- Total tests: 11 (flipping contract uses 6 primary row-count/isolation tests)
- q/x7q.sql: 2/6 = 0.33
- q/m2p.sql: 2/6 = 0.33
- v/h3v.sql: 2/6 = 0.33
- Cap: 0.5. Status: PASS

### Per-test feasibility pre-check
All tests LOW risk; multiple valid fix orderings; isolation consolidated in test_no_scenario_leaks.
