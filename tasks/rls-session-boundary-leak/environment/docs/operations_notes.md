# Operations notes

The backend stores customer records in PostgreSQL 15 under `/app/store`.
Application connections authenticate as `svc_runner`, set the `app.scope_id`
variable through `/app/app/session_set.sh`, and read through filters in
`/app/q`. Row filters on the core tables should keep each catalog label from
reading another label's rows.

The audit matrix under `/app/app/audit_runner.sh` exercises ad-hoc and pooled
access paths. Pooled paths reuse server-side statement handles across scope
changes. The runner reports a `catalog_compliance` block alongside the scenario
results. See `/app/docs/planner_notes.md` for how generic plans interact with
session GUC changes on reused handles.

Candidate filter bundles under `/app/q/m2p_candidate.sql` and legacy accessors
under `/app/q/w2_legacy.sql` are retained for review only and are not loaded at
bootstrap.

Role configuration for `svc_runner` and `svc_reader` is applied via `/app/v/`.
Query `SELECT array_to_string(rolconfig, ',') FROM pg_roles WHERE rolname='svc_runner'`
to inspect active settings; entries use the compact form, e.g.
`plan_cache_mode=force_custom_plan`, `statement_timeout=60s`.
The `svc_reader` role uses `default_transaction_read_only=on` to enforce
read-only access on all borrowed connections.

When onboarding a new catalog label, load its row into `org_dim` before granting
the application profile access.
