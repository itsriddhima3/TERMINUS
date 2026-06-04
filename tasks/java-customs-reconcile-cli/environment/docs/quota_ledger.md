# Quota ledger interaction

When `/api/v1/quota/:hs10` returns `"blocked": true`, the bench applies a statutory uplift on expected duty:

`expected_duty_usd = declared_value * fx_to_usd * (tariff_pct / 100) * quota_uplift_multiplier`

Read `quota_uplift_multiplier` from `/app/config/bench_policy.toml` (1.15 for SHIP-2024-Q1).

Underpaid detection compares declared duty against that uplifted expectation. Ignoring the uplift understates exposure on quota-blocked lines.
