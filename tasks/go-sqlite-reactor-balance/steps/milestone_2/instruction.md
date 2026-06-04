Once SCN-Alpha loads cleanly, `fluxctl set` must enforce relational move gates before writing cell levels; metrics should change only on `fluxctl tick`.

Illegal same-kind jumps, corner overshoots, and kind-ceiling violations still land in the database, and some legal moves are rejected. Display helpers under `/app/decoy/` and `/app/hub/` do not reflect live gate order.

Restore move validation to match the ranked gate definitions in `/app/docs/catalog/` and the worked coupling examples there. When you're done, signal completion.
