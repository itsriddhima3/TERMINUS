# Catalog part 03 — P2 persist dimension

P2 lives in the `p4v` crate root and wraps sqlite insert attempts for ffprobe-derived facts.

`[p2]` in `/app/config/bench_profiles.toml` defines:

- `min_busy_retry_attempts`: count of insert attempts before giving up on `SQLITE_BUSY` (not counting successful early exit).
- `initial_backoff_ms` then exponential doubling until `max_backoff_ms` between busy attempts.
- `record_busy_in_meta_on_final_failure`: when true, increment `meta.busy_events` only on the final failed busy after exhausting attempts.

A shallow loop that sleeps once or exits after two attempts violates P2 even when other dimensions read in-profile on a manual probe. High `busy_events` with incomplete row totals indicate P2 numeric gaps per `[p2]`.
