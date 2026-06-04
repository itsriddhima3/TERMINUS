# Move policy

Level changes go through relational gates before persisting. Authoritative rank ordering and coupling semantics live in **catalog memo 02** (`/app/docs/catalog/part_02_gate_lattice.md`). Worked edge vs diagonal examples are in `/app/docs/catalog/examples.md`.

## Gate kinds (summary)

| rule_type         | Org name (catalog) |
|-------------------|--------------------|
| `adjacency_delta` | edge-kind coupling |
| `corner_cap`      | corner envelope    |
| `type_max`        | kind ceiling       |

## Component kinds

- **pump** — drives metric_a (heat) up and metric_c down on each tick
- **rod** — pulls metric_a down and metric_b (pressure) up on each tick
- **vent** — pulls metric_b down and metric_c (outward flow) up on each tick

Illegal moves must leave the database unchanged. Legal moves update only the targeted cell level; metrics change only after `tick`.

Display-only ordering from `/app/decoy/q3l` and `/app/hub/r5v` is not authoritative.
