# Connection pool observations

Production poolers keep server-side handles open across checkout cycles.
Checkout assigns `app.scope_id` immediately before `EXECUTE`. When the prior
checkout used the same handle with a different scope value, the generic plan
may still reflect the first tenant that warmed the handle.

Warm-cache jobs under `/app/app/warm_cache.sh` mimic startup preparation at
scope 1 before the first customer checkout. This matches the `warm_cache_first`
audit row when isolation regresses.

The probe helper `/app/app/probe_plan_mode.sh` prints the effective
`plan_cache_mode` for the current session without mutating filter definitions.
