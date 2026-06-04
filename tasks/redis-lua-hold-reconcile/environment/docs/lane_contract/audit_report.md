# Stock audit report contract

`/app/output/stock_audit.json` is produced by `/app/app/stock_audit.sh`. Scenario names match the keys in `/app/data/scenario_matrix.json` (twenty rows): solo_lane, burst_dual, burst_quad, mixed_skus, zero_floor, pipe_burst, retry_lane, reject_over_cap, gamma_solo, beta_solo, alpha_edge, stress_fan, stagger_race, triple_interleave, unit_rush, two_phase_drain, canonical_drift, odd_remainder, bimodal_burst, saturated_fan.

## Top-level object

| field | type | notes |
|-------|------|-------|
| schema_version | integer | must be 1 |
| catalog_skus | array of strings | Alpha-Unit, Beta-Crate, Gamma-Tote in catalog order |
| scenarios | object | keyed by matrix scenario name |
| stock_compliance | object | lane binding and frame posture probes |
| stress_summary | object | aggregate oversell tally |

Fields such as `oversell_detected`, `total_granted`, `final_stock`, and `requests_attempted` appear inside each `scenarios[<name>]` row, not at the JSON root.

## Scenario row

| field | type | notes |
|-------|------|-------|
| oversell_detected | boolean | false when the lane stayed within cap |
| total_granted | integer | units successfully reserved |
| final_stock | integer | remaining units on the worker slot after the scenario |
| requests_attempted | integer | grant attempts executed |
| sku | string | catalog label, or `mixed` / `triple` for multi-lane rows |

## stock_compliance

These probes are graded independently of scenario oversell flags. Clean scenario rows alone are not sufficient when any compliance field still reflects the broken baseline.

| field | type | expected after repair |
|-------|------|------------------------|
| canonical_keys_seeded | boolean | true |
| worker_slot_is_alias | boolean | must not be true |
| forward_observation_frame | boolean | must not be true |

After the audit completes, live Redis values at worker slot keys must match the catalog seed keys for every SKU label.

## stress_summary

| field | type | expected after repair |
|-------|------|------------------------|
| oversell_events | integer | 0 |
| scenario_count | integer | 20 |

## Inventory rules

Opening counts come from `/app/data/sku_catalog.json`: Alpha-Unit six, Beta-Crate ten, Gamma-Tote four.

- Every scenario row must have `oversell_detected` false, non-negative `final_stock`, and `total_granted` at or below the applicable opening cap (combined caps for `mixed_skus` and `triple_interleave`).
- Single-SKU lanes must conserve inventory: `total_granted + final_stock` equals that SKU's opening count.
- When demand meets or exceeds a lane cap, `unit_rush` and `odd_remainder` on Beta-Crate must grant all ten opening units; `saturated_fan` on Alpha-Unit must grant all six.
