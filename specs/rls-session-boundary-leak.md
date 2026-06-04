### Decision
GO — Attempt 1. PostgreSQL multi-tenant RLS plan-cache leak with distributed fix surface across policies, scope accessor, and role plan-cache settings.

### Metadata
- version: 2
- Task name: rls-session-boundary-leak
- Title: RLS Session Boundary Leak
- Category: security
- Languages: ["bash", "sql"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["db_interaction"]
- Tags: ["postgresql", "rls", "multi-tenant", "sql", "isolation"]
- Milestones: 0

## Authoring Brief

### Public contract
Agent receives a PostgreSQL 15 SaaS schema with row filters keyed off session variable `app.scope_id`. Running `/app/app/audit_runner.sh` writes `/app/output/boundary_audit.json` with `schema_version` 1, `catalog_labels` for Acme-Crate / Beta-Tote / Delta-Bin, and six scenario rows (`adhoc_single`, `reuse_stmt`, `pool_rotate`, `join_path`, `view_path`, `batch_fetch`). Each scenario reports `cross_scope_visible`, `foreign_labels_seen`, and `owned_row_count`. Several pooled / prepared-statement paths leak foreign labels after context switches; ad-hoc single-context reads appear fine. Agent must repair the database layer so every scenario reports `cross_scope_visible: false` with empty `foreign_labels_seen`.

### Failure topology
Symptoms cluster around reused server-side statement handles and pooled rotation: scope switches do not re-bind row filters while generic plans remain cached. Ad-hoc paths mask the defect. Ledger, contacts, inventory, and audit tables share the same filter pattern; a security-barrier view inherits the broken behavior. A dormant scope accessor exists but is not wired into policies. Role-level execution settings interact with prepared-statement planning.

### Environment shape
Dockerized PostgreSQL 15 app tree under `/app`: SQL schema and seed bundles, function helpers, role definitions, view definitions, bash audit/scenario runners, connection helpers, org catalog JSON, and operations notes. Tests invoke the audit runner against live database state.

### Required artifacts
Standard single-step layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (20+ files), `solution/solve.sh`, `tests/test.sh`, `tests/test_outputs.py`.

### Test plan
- `test_report_schema_version` — schema_version equals 1
- `test_catalog_labels_present` — three catalog labels in order
- `test_all_scenarios_present` — six scenario keys exist
- `test_adhoc_single_isolated` — no leak; owned_row_count sane
- `test_reuse_stmt_isolated` — prepared reuse after switch isolated to Beta-Tote (2 rows)
- `test_pool_rotate_isolated` — pooled rotation isolated to Delta-Bin (4 rows)
- `test_join_path_isolated` — join after switch isolated to Delta-Bin
- `test_view_path_isolated` — view path after switch isolated to Acme-Crate
- `test_batch_fetch_isolated` — batch fetch after switch isolated to Beta-Tote
- `test_no_scenario_leaks` — all scenarios false/empty foreign labels
- `test_foreign_labels_are_strings` — type sanity on label arrays

### Drafting guardrails
Instruction stays symptoms-only: no VOLATILE/STABLE vocabulary, no plan_cache_mode recipe, no policy file paths. Fix-path symbols opaque (`fn_k7`, `op_m3`, `cfg_p9`). Decoy helper `op_m3_for_session` mirrors session reads but is not the primary fix locus.

### Triviality Ledger

- Wiring the existing STABLE accessor without changing volatility or role plan-cache settings passes ad-hoc tests but fails prepared-statement scenarios because generic plans still bind the first scope.
- Setting only `force_custom_plan` on the role while policies still inline session reads may appear fixed on some paths but fails join/view scenarios when policies remain uncoupled from a per-execution accessor.
- Disabling RLS or granting superuser to the app role would satisfy row counts but violates forced RLS on base tables (tests still run as restricted role).

### Per-gate Pitfall Inventory

- RC1 — Oracle must alter function volatility, rebind all four policies, and set role plan_cache_mode; not a one-line revert.
- RC6 — Instruction must not name plan caching, VOLATILE, or policy file paths.
- RC7 — solve.sh includes substantive SQL for all policies plus role setting (≥30 LOC).
- CR1/CR7 — Use committed symbol names `fn_k7`, `pol_*` policy family; no instruction nouns in fix-path identifiers.
- CR2 — flipping_point_contract splits policy rebind, fn_k7 volatility, and svc_runner plan_cache_mode across test subsets.
- GX9 — Ground Acme/Beta/Delta active counts (2/2/4) in instruction before tests assert owned_row_count.

### Initial Draft Commitments

- `tasks/rls-session-boundary-leak/instruction.md`
- `tasks/rls-session-boundary-leak/task.toml`
- `tasks/rls-session-boundary-leak/output_contract.toml`
- `tasks/rls-session-boundary-leak/environment/Dockerfile`
- `tasks/rls-session-boundary-leak/environment/init/docker-entrypoint-wrapper.sh`
- `tasks/rls-session-boundary-leak/environment/init/ensure_pg.sh`
- `tasks/rls-session-boundary-leak/environment/init/bootstrap.sh`
- `tasks/rls-session-boundary-leak/environment/init/post_boot.sh`
- `tasks/rls-session-boundary-leak/environment/schema/001_extensions.sql` through `008_seed_data.sql`
- `tasks/rls-session-boundary-leak/environment/functions/scope_reader.sql`
- `tasks/rls-session-boundary-leak/environment/functions/auth_helpers.sql`
- `tasks/rls-session-boundary-leak/environment/functions/audit_scalar.sql`
- `tasks/rls-session-boundary-leak/environment/roles/app_role.sql`
- `tasks/rls-session-boundary-leak/environment/roles/reader_role.sql`
- `tasks/rls-session-boundary-leak/environment/config/postgresql.conf.snippet`
- `tasks/rls-session-boundary-leak/environment/config/pg_hba.conf.snippet`
- `tasks/rls-session-boundary-leak/environment/app/audit_runner.sh`
- `tasks/rls-session-boundary-leak/environment/app/scenario_a.sh` through `scenario_f.sh`
- `tasks/rls-session-boundary-leak/environment/app/pool_sim.sh`
- `tasks/rls-session-boundary-leak/environment/app/session_set.sh`
- `tasks/rls-session-boundary-leak/environment/lib/psql_wrap.sh`
- `tasks/rls-session-boundary-leak/environment/lib/conn_init.sh`
- `tasks/rls-session-boundary-leak/environment/lib/result_collect.sh`
- `tasks/rls-session-boundary-leak/environment/data/org_catalog.json`
- `tasks/rls-session-boundary-leak/environment/data/scenario_matrix.json`
- `tasks/rls-session-boundary-leak/environment/migrations/baseline.sql`
- `tasks/rls-session-boundary-leak/environment/migrations/v2_views.sql`
- `tasks/rls-session-boundary-leak/environment/views/active_orders.sql`
- `tasks/rls-session-boundary-leak/environment/views/org_summary.sql`
- `tasks/rls-session-boundary-leak/environment/docs/operations_notes.md`
- `tasks/rls-session-boundary-leak/solution/solve.sh`
- `tasks/rls-session-boundary-leak/tests/test.sh`
- `tasks/rls-session-boundary-leak/tests/test_outputs.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/functions/scope_reader.sql
  symbol: fn_k7
  kind: function
  signature: fn_k7() RETURNS integer LANGUAGE sql
  purpose: returns session scope integer from app.scope_id GUC

- path: environment/schema/006_policies.sql
  symbol: pol_ledger_read
  kind: function
  signature: POLICY pol_ledger_read ON ledger FOR SELECT USING (org_ref = fn_k7())
  purpose: row filter on ledger reads

- path: environment/schema/006_policies.sql
  symbol: pol_contacts_read
  kind: function
  signature: POLICY pol_contacts_read ON contacts FOR SELECT USING (org_ref = fn_k7())
  purpose: row filter on contacts reads

- path: environment/roles/app_role.sql
  symbol: svc_runner
  kind: constant
  signature: ALTER ROLE svc_runner SET plan_cache_mode = force_custom_plan
  purpose: per-role prepared-statement planning mode
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/functions/scope_reader.sql
    controls_tests: [test_reuse_stmt_isolated, test_batch_fetch_isolated]
  - id: B
    path: environment/schema/006_policies.sql
    controls_tests: [test_join_path_isolated, test_view_path_isolated]
  - id: C
    path: environment/roles/app_role.sql
    controls_tests: [test_pool_rotate_isolated, test_adhoc_single_isolated]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/functions/auth_helpers.sql
  kind: helper
  rhymes_with: fn_k7
  non_fix_purpose: op_m3_for_session reads scope for audit existence checks only

- path: environment/functions/audit_scalar.sql
  kind: helper
  rhymes_with: fn_k7
  non_fix_purpose: cfg_p9 and audit_scalar_total support reporting aggregates
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [saas, backend, postgresql, customer, organization, records, catalog, acme-crate, beta-tote, delta-bin, audit, runner, boundary, json, schema, version, labels, scenarios, cross_scope_visible, foreign_labels_seen, owned_row_count, patterns, connection, session, context, prepared, query, pooled, rows, database, matrix, grading, isolation, ledger, entries, switch, access, switch, repair, layer, active, foreign, labels, empty, scope, filtering, organizations]
```
