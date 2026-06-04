# Delta and reconciliation rules

Impossible-delta events fire when consecutive **corrected** cumulative stamps on the same device (sorted by `reading_at`, stream order for ties) increase by more than `max_delta_kwh_per_interval` plus `delta_tolerance_kwh` from bench policy. Negative ledger adjustments can create a large forward step on the **next** row at the same stamp — evaluate those chains on corrected values, not raw registers.

Corrections from `GET /api/v1/corrections` supply `delta_kwh` per (`device_id`, `reading_at`). Apply to every row at that stamp — see `/app/docs/correction_ledger.md`.

`reconcile.json` top-level keys: `meter_id`, `gap_events`, `duplicate_events`, `impossible_delta_events`, `cost_by_site`.

`gap_events` entries carry `device_id`, `expected_at`, `reading_at`, and `gap_minutes`. `duplicate_events` entries carry `device_id`, `reading_at`, and `register_kwh` (corrected stamp). `impossible_delta_events` entries carry `device_id`, `reading_at`, `delta_kwh`, and `max_delta_kwh_per_interval`.

`normalized.csv` columns: `device_id`, `reading_at`, `register_kwh`, `site_id`, `rate_cents`, `issue` — use literal `gap`, `duplicate`, `impossible_delta`, or leave empty when clean.

`cost_by_site` follows `/app/docs/cost_basis.md`.
