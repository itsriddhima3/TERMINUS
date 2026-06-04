# Catalog worked examples — edge-kind coupling

Grid coordinates are 0-based. Edge adjacency is Manhattan-only.

## Example A — diagonal rods do not couple

SCN-Alpha places rods at `(0,1)` and `(1,0)`. They are diagonal neighbors. Raising `(0,1)` to level 3 while `(1,0)` stays at 1 does **not** invoke edge-kind coupling (no shared edge). Corner and kind-ceiling gates may still apply on other cells.

## Example B — vertical rod pair

SCN-Alpha also aligns rods at `(0,1)` and `(1,1)` (edge-adjacent). With `(1,1)` at level 1:

- `set 0 1 2` is permitted (delta 1, band width 1).
- `set 0 1 3` is rejected (delta 2 > band width 1).

After both sit at level 2, `set 0 1 0` is rejected because delta against `(1,1)` is 2.

## Example C — corner envelope vs kind ceiling

Corner `(0,0)` pump: envelope rank 20 caps level at 2 even though kind ceiling allows 3. Non-corner `(0,2)` vent may reach kind ceiling 3 when no coupling violation exists.
