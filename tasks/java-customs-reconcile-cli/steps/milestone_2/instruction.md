With a correct `/app/var/shipments.json`, `customsctl enrich SHIP-2024-Q1` should query the local reference service and write `/app/var/enriched.json`.

Enrichment today drifts from fixtures: tariff percentages can be absent for valid `hs10` keys, `fx_to_usd` does not match the multiplier table, and quota flags may be wrong even when `/health` is fine. Compare live `GET` responses on port 3921 to the written JSON — `/app/docs/fx_table_notes.md` and `/app/docs/api_contract.md` disagree on FX direction.

Repair enrichment so each line carries tariff_pct, fx_to_usd, quota_blocked, and classification_missing consistent with the service for SHIP-2024-Q1. When tariff lookup returns not_found, set classification_missing true and leave both tariff_pct and quota_blocked as JSON null (skip quota for that line); still populate fx_to_usd. See `/app/docs/api_contract.md`.

When you're done, **signal completion** and include the command you used to regenerate enriched output.
