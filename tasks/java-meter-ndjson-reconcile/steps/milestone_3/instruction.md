Given `/app/var/normalized.json`, run `/app/bin/meterctl reconcile MTR-2024-Q1` to emit `/app/output/reconcile.json` and `/app/output/normalized.csv`.

Reconciliation output is wrong today: interval gaps go unreported, duplicate timestamps slip through, register surges after ledger adjustments stay invisible, and `cost_by_site` under-bills interval energy. Operator notes under `/app/docs/` disagree on gap slots, delta chains, and cost basis.

`reconcile.json` needs `meter_id` (`MTR-2024-Q1`), `gap_events`, `duplicate_events`, `impossible_delta_events`, and `cost_by_site`. `normalized.csv` columns are `device_id`, `reading_at`, `register_kwh`, `site_id`, `rate_cents`, and `issue` — use literal `gap`, `duplicate`, or `impossible_delta` when flagged, otherwise leave empty. When you're done, **signal completion** and include the command you used to regenerate both outputs.
