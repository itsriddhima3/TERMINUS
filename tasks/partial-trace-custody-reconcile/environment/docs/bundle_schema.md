# Custody bundle schema

The sweep writes `/app/output/custody_bundle.json` as UTF-8 JSON with one trailing newline.

## Top level

| Key | Type | Description |
|-----|------|-------------|
| `run_id` | string | Lowercase hex, 16 characters, stable for a given pack set and ledger contents |
| `packs` | array | One object per scenario pack, sorted by `pack_id` ascending |
| `aggregate` | object | Cross-pack totals |

## Pack object

| Field | Type | Description |
|-------|------|-------------|
| `pack_id` | string | Matches `meta.json` pack id |
| `transition_ledger` | array | Movement rows sorted by `(object, tick, from, to)` |
| `consistency_proof` | object | Proof block derived from the ledger |
| `pack_ok` | boolean | True when all proof booleans pass and ledger is complete |

## Transition row

| Field | Type | Description |
|-------|------|-------------|
| `tick` | integer | Virtual tick when movement occurred |
| `object` | string | Unit id |
| `from` | string | Prior holder id |
| `to` | string | New holder id |
| `inferred` | boolean | False when sourced from an explicit handoff line in any channel; true when reconstructed to bridge partial sightings |

## Consistency proof

| Field | Type | Description |
|-------|------|-------------|
| `single_holder_ok` | boolean | After conflict resolution, each object has at most one holder per tick |
| `acyclic_ok` | boolean | For each object, consecutive ledger rows chain (`to` of row *i* equals `from` of row *i+1*) with non-decreasing ticks |
| `gap_fill_count` | integer | Count of ledger rows with `inferred` true |
| `contradiction_resolved` | integer | Count of `(tick, object)` pairs where multiple channels disagreed before rank resolution |
| `ledger_digest` | string | Lowercase hex SHA-256, 64 characters, over canonical JSON of the ledger array (`sort_keys`, compact separators, UTF-8) |

## Aggregate object

| Field | Type | Description |
|-------|------|-------------|
| `failed_packs` | integer | Count of packs with `pack_ok` false |
| `failed_pack_ids` | array | Sorted lexicographic ids of failed packs |

Per-pack fragment files may appear under `/app/output/.pack_<id>.json` during the sweep; the merged bundle is authoritative for grading.
