Given `/app/var/enriched.json`, `customsctl reconcile SHIP-2024-Q1` must emit `/app/output/reconcile.json` and `/app/output/reconcile.csv`.

Reconciliation output is wrong today: underpaid detection skips FX conversion on enriched rows, quota-blocked lines understate expected duty, and missing-classification findings do not add the bench placeholder exposure into importer roll-ups. Importer exposure totals for SHIP-2024-Q1 should match what you get by applying `/app/config/bench_policy.toml` and the precedence order in `/app/docs/bench_precedence.md` — not the retired annexes under `/app/docs/archive/`.

Align behavior with `/app/docs/duty_rules.md`, `/app/docs/value_basis.md`, and `/app/docs/quota_ledger.md` (underpaid tolerance from `/app/config/run.toml`). reconcile.json needs top-level `batch_id` (SHIP-2024-Q1), `underpaid_lines`, `missing_classifications`, and `exposure_by_importer`. reconcile.csv columns are line_id, importer_id, issue, and exposure_usd per finding; issue must be the literal `underpaid` or `missing` (not a longer label).

When you're done, **signal completion** and include the command you used to regenerate both outputs.
