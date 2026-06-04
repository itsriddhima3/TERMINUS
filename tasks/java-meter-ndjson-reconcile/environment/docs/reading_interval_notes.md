# Reading interval notes

Each device emits register readings on a fixed cadence (`interval_min`, typically 15).
For a given `device_id`, consecutive `reading_at` values should advance by one interval unless a gap event is recorded.

Older bench exports flagged gaps when clock span exceeded **twice** `gap_tolerance_min` from `/app/config/bench_policy.toml`. That legacy threshold is archived under `/app/docs/archive/interval_gap_legacy.md`. Authoritative gap rules live in `/app/docs/gap_slot_semantics.md`.

Duplicate detection uses the key fields listed under `[reconciliation]` in bench policy (`device_id` + `reading_at`). Two rows sharing both fields are duplicate events even when `register_kwh` differs.
