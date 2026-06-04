# Gap slot semantics

Gap detection walks each device chain sorted by `reading_at`. Compare clock minutes between consecutive rows. When the span strictly exceeds the **prior row's** `interval_min` (not the global policy tolerance alone), emit:

- `device_id`
- `expected_at` — the missing slot timestamp one interval after the prior row
- `reading_at` — the later observed stamp where the gap ends
- `gap_minutes` — span minus prior row interval

CSV `issue=gap` tags the later observed row (`reading_at`), not the missing slot.

Legacy operator notes that multiply `/app/config/bench_policy.toml` `gap_tolerance_min` by two are retired — see `/app/docs/archive/interval_gap_legacy.md`.
