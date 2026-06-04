# Storage contract

The on-disk catalog lives at `/app/var/game.db`. All operator commands read and write through that single SQLite file.

## Meta markers

The `meta` table stores string keys. The active catalog revision is recorded under key `schema_version`. Bench notes under `/app/docs/bench_precedence.md` define the expected revision marker for new installs.

## Relational layout

| Table        | Role |
|--------------|------|
| `meta`       | Key/value markers including catalog revision |
| `chambers`   | Fixed slot kinds for each scenario grid cell |
| `components` | Mutable per-cell levels bound to chamber kinds |
| `constraints`| Per-kind level bounds for a scenario |
| `rules`      | Precedence-ordered move gates |
| `scenarios`  | Opening metric triple, band windows, loss cutoffs, stable streak requirement |
| `sessions`   | Named slots (`active` plus user save slots) holding tick index, metrics, streak, outcome flags |

Metric columns use opaque names `metric_a`, `metric_b`, and `metric_c`. Field manuals map these to heat, pressure, and outward flow respectively.

## Session slots

Slot `active` tracks the live playthrough. Named slots from `save`/`load` must round-trip tick count, the three metrics, component levels, and stable streak.
