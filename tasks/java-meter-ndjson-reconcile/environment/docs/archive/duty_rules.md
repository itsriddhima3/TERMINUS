# Duty reconciliation

Expected duty (USD) starts from the statutory value basis in `/app/docs/value_basis.md`, then:

`core = basis_value * fx_to_usd * (tariff_pct / 100)`

When quota is blocked, multiply core by `quota_uplift_multiplier` from `/app/config/bench_policy.toml` (see `/app/docs/quota_ledger.md`).

A line is **underpaid** when `declared_duty + tolerance` is below expected duty (`tolerance` from `/app/config/run.toml`).

**Missing classification** when the tariff endpoint returns not_found for the line's `hs10`.

**Exposure by importer** sums `max(0, expected_duty - declared_duty)` across that importer's lines (underpaid lines only).

## Output shapes

`reconcile.json` top-level keys: `batch_id`, `underpaid_lines`, `missing_classifications`, `exposure_by_importer`.

`reconcile.csv` header: `line_id,importer_id,issue,exposure_usd` with one row per underpaid or missing-classification finding. The `issue` column uses exact literals only: `underpaid` for duty-gap rows; `missing` for lines listed in `missing_classifications` (not a longer label such as `missing classification`).

Recompute underpaid sets, per-line exposure, and importer roll-ups from the current enriched manifest and bench policy on every run — do not cache prior totals.
