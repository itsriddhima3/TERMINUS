# Bundle schema

The sweep writes `/app/output/verdict_bundle.json` with the following top-level keys:

| Key | Type | Description |
|-----|------|-------------|
| `run_id` | string | Stable sweep identifier (hex, 16 chars) |
| `packs` | array | One object per registry pack, in registry order |
| `aggregate` | object | Cross-pack counters |

## Pack object

| Field | Type | Description |
|-------|------|-------------|
| `pack_id` | string | Registry id |
| `pack_rc` | integer | 0 when every row `handoff_ok` is true, else 1 |
| `rows` | array | Service rows audited in this pack |

## Row object

| Field | Type | Description |
|-------|------|-------------|
| `row_id` | string | Node id from the sketch |
| `route_state` | string | `cleared`, `blocked`, or `held` |
| `window_state` | string | `live`, `preopen`, or `expired` |
| `identity_hex` | string | Lowercase hex fingerprint of leaf material (64 chars for SHA-256 class) |
| `chain_ok` | boolean | OpenSSL verify/store succeeded for the row |
| `walk_ok` | boolean | Anchor reachability via the correct edge family |
| `handoff_ok` | boolean | Conjunction of policy checks for the row |
| `path_ids` | array | Node ids from the service row node toward anchor (service row node first, anchor last); empty `[]` when the service row node IS the anchor (no intermediate hops required) |
| `ledger_hits` | integer | Count of deny-family edges touching the row |

## Aggregate object

| Field | Type | Description |
|-------|------|-------------|
| `failed_packs` | integer | Count of packs with `pack_rc` != 0 |
| `failed_pack_ids` | array | Sorted lexicographic pack ids with failures |
