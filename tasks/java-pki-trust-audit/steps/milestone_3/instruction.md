Graph export should turn `/app/output/audit_results.json` into `/app/output/trust.dot` and `/app/output/trust.svg`, but rendered diagrams disagree with the styling annex in `/app/docs/pki_ops_dossier/part_05.md` (section 9.2). The DOT file must declare a `digraph`, use `forestgreen` edges on accepted paths, and apply role-specific `fillcolor` on nodes; the SVG must be a valid render of that graph and must exceed 500 bytes.

Update `trust.graph.emit.StyleLedger` role attributes to match section 9.2: `valid_path` nodes use `fillcolor="#e8f5e9"`; accepted subgraph edges use `color=forestgreen`; `expired_root` nodes use `fillcolor=gray` with `style=dashed`; `revoked_intermediate` nodes use `color=red`, `penwidth=2`, and `peripheries=2`; `rejected` leaf nodes (for example `path_too_deep` and `not_yet_valid_leaf` end entities) use `fillcolor=orange` with `style=filled`.

Each node ID is formed by replacing hyphens in the certificate CN with underscores, then appending an underscore and the case ID — for example, `bench-int-revoked` in case `revoked_intermediate` becomes `bench_int_revoked_revoked_intermediate`, and `bench-leaf-deep` in case `path_too_deep` becomes `bench_leaf_deep_path_too_deep`.

When you're done, **signal completion**.
