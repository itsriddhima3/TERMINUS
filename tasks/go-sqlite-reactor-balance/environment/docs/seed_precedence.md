# Seed precedence

Seed TOML files under `/app/data/seeds/` are authoritative for opening layout and numeric targets when a scenario is initialized.

## File naming

Each file is named `<scenario-id>.toml`. The `init --scenario` flag selects which file loads.

## Sections

- `opening` — starting `metric_a`, `metric_b`, `metric_c`, and `stable_needed`
- `bands` — inclusive low/high pairs for each metric
- `loss` — breach thresholds (metrics at or above these values end the run)
- `grid` — nine `row`/`col` entries with `kind` (`pump`, `rod`, `vent`) and `level`
- `constraints` — per-kind min/max levels copied into the catalog
- `rules` — precedence-ranked gate definitions copied into the catalog

When seed rows disagree with archived prose, `/app/docs/bench_precedence.md` wins. Constraint lattice and gate roster materialization semantics are defined in catalog memo 01; ranked evaluation in memo 02.
