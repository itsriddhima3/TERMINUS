# Marked sketch styles

Colorized copies land under `/app/output/marked/<pack_id>.dot`. Nodes gain a `fillcolor` token from this table:

| Token | When applied |
|-------|----------------|
| `deny_fill` | Row has ledger hits or `route_state` is `blocked` |
| `live_fill` | `window_state` is `live` and row not blocked |
| `cleared_fill` | `route_state` is `cleared` |

Edges are not recolored. Original node ids must be preserved verbatim.
