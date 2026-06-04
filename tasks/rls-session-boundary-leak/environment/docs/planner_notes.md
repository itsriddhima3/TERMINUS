# Planner notes (PostgreSQL 15)

Reference material for how the audit harness exercises pooled and ad-hoc access paths.

## Generic versus custom plans

Prepared statements may choose a **generic plan** after several executions with
`plan_cache_mode = auto`. Generic plans reuse qual evaluation from the first
planning snapshot. Session variables referenced directly inside row-security
quals participate in that snapshot.

The audit harness sets `plan_cache_mode = force_generic_plan` on several paths
to mirror connection pooler behavior: a handle prepared under one `app.scope_id`
value is reused after the pool assigns a different tenant context on the same
TCP session.

## Expression volatility and planning

Functions marked **STABLE** or **IMMUTABLE** may be folded into the plan during
generic planning. Wrappers around `current_setting()` inherit planner treatment
from their volatility class even when row filters are later rewritten to call
the wrapper instead of inlining the GUC read.

## Role defaults versus session overrides

Profile defaults under `/app/v` apply to login roles. Individual audit sessions
may still override `plan_cache_mode` for the lifetime of the pooled connection.
Throughput tuning notes in the profile bundle intentionally defer custom-plan
forcing until after pool metrics justify the regression.

## Related reading

PostgreSQL 15 documentation: `PREPARE`, `plan_cache_mode`, `CREATE POLICY`,
and function volatility categories (`VOLATILE`, `STABLE`, `IMMUTABLE`).
