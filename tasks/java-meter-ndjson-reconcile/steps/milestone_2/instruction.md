With a correct `/app/var/readings.json`, run `/app/bin/meterctl normalize MTR-2024-Q1` to write `/app/var/normalized.json` using `/app/data/devices.csv`, `/app/data/tariffs.csv`, and correction events from the Spring Boot service on port 8080.

Each row keeps fetch columns plus `site_id`, `rate_cents`, `max_delta_kwh_per_interval`, and `corrected_register_kwh`. Enrichment drifts today: catalog joins miss `site_id`, tariff windows pick the wrong band, and ledger deltas behave inconsistently on duplicate timestamps even when `/health` is fine. Notes under `/app/docs/` disagree on joins, tariff windows, and correction application.

Repair normalization for `MTR-2024-Q1`. When you're done, **signal completion** and include the command you used to regenerate normalized output.
