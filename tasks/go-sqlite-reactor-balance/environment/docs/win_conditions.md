# Win and loss conditions

After each `tick`, the engine evaluates the active metric triple against the scenario row in the catalog.

Authoritative dwell counter, victory coupling, and breach cutoff semantics are in **catalog memo 03** (`/app/docs/catalog/part_03_dwell_outcome.md`). Session archive requirements are in memo 04.

## Stable bands (summary)

Each scenario stores inclusive band windows for `metric_a`, `metric_b`, and `metric_c`. All three must sit inside their windows simultaneously for a tick to count as stable.

## Victory (summary)

Victory requires consecutive stable ticks per the scenario's `stable_needed` field. The dwell counter resets when any metric leaves band.

## Loss (summary)

Loss triggers on breach cutoffs from the scenario row (`loss_*` columns), not band upper bounds.

## Persistence (summary)

Outcome flags and dwell counter live in the `active` session row and must survive `save`/`load` for named slots including level snapshots per memo 04.
