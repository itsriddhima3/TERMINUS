# Local reference service

Base URL: `http://127.0.0.1:3921`

- `GET /health` → `{ "ok": true }`
- `GET /api/v1/tariff/:hs10` → `{ "hs10", "rate_pct" }` or 404
- `GET /api/v1/fx/:ccy` → `{ "currency", "fx_to_usd" }` (multiply declared value by this factor to reach USD)
- `GET /api/v1/quota/:hs10` → `{ "hs10", "blocked" }`
- `GET /api/v1/batch/:batchId` → `{ "batch_id", "lines", "legacy_rows" }` (use `lines`, not `legacy_rows`; each line carries raw `hs_raw` and `currency_raw` from the shipment CSV — normalize before persistence)

## Enrichment field contract

Each `enriched.json` line carries `tariff_pct`, `fx_to_usd`, `quota_blocked`, and `classification_missing` from live `GET` responses:

- Tariff **404** (`not_found`): set `classification_missing` to `true`, leave `tariff_pct` as JSON `null`, and leave `quota_blocked` as JSON `null` (do not call quota for that line; do not write `false`).
- Tariff **200**: set `classification_missing` to `false`, copy `rate_pct` into `tariff_pct`, then call quota and store `blocked` as `quota_blocked` (`true` or `false`).
- FX: always fetch `fx_to_usd` for the line currency, including when tariff returns 404.
