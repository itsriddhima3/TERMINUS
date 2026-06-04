# Catalog memo 02 — gate lattice evaluation

Move gates execute in **ascending priority rank** (lower number first). The SCN-Alpha roster uses three ranks:

| Rank | rule_type | Org name | Param |
|------|-----------|----------|-------|
| 10 | `adjacency_delta` | edge-kind coupling | `param_a` = coupling band width |
| 20 | `corner_cap` | corner envelope | `param_a` = max level at corners |
| 30 | `type_max` | kind ceiling | uses `constraints.max_level` |

## Edge-kind coupling (adjacency_delta)

Only **edge-adjacent** cells (Manhattan distance 1) participate. Diagonal neighbors never couple.

Among edge neighbors sharing the same `kind`, let `delta = abs(proposed_level - neighbor_level)`. The move is rejected when **`delta` is strictly greater than `param_a`**. A delta **equal** to `param_a` is permitted when the band width is one.

## Corner envelope (corner_cap)

Cells `(0,0)`, `(0,2)`, `(2,0)`, `(2,2)` may not exceed `param_a` (SCN-Alpha uses envelope **2**).

## Kind ceiling (type_max)

Proposed level must not exceed the scenario constraint row for that cell's kind.

Illegal moves must not mutate `components`. Metrics change only after `tick`.
