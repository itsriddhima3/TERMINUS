# Spine predicate registry

Workload `WK-SPINE-EMEA` applies two spine predicates before grouping:

- region equals `EMEA`
- event_type equals `purchase`

## events collection

Columns: shard_id, region, event_type, value, seq.

Spine predicate: yes for region and event_type pair above.

## metrics_snap collection

Columns: lane, reading, seq.

Spine predicate: no — used by hourly beta rollup only.
