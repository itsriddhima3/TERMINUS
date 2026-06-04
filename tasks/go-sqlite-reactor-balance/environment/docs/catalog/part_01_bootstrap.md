# Catalog memo 01 — bootstrap materialization

## Revision marker B2

Fresh installs must record catalog revision **B2** in `meta` under key `schema_version` with string value **`2`**. Older archive drafts referenced revision **B1** (`1`); those markers indicate incomplete materialization.

## Chamber mirror and level binding

Initialization copies all nine chamber rows from the scenario seed TOML. The companion `components` rows must bind **`level` from the seed cell level field**, not from grid row ordinals or column indices. Operators report pumps at corners showing row indices (0, 1, 2) instead of seeded levels when binding is wrong.

## Constraint lattice

Each scenario requires three `constraints` rows — one per kind (`pump`, `rod`, `vent`) — carrying `min_level` and `max_level` copied from the seed `[constraints]` table.

## Gate roster

Ranked `rules` rows must be present after init (priorities **10**, **20**, **30** for the standard SCN-Alpha roster). An empty roster causes move acceptance to become permissive: edge-kind violations and corner overshoots slip through silently.

## Idempotence

Re-running `init` for the same scenario must yield an identical catalog fingerprint (chambers, components, constraints, rules, scenarios).
