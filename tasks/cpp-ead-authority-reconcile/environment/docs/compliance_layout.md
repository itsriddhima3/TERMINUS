# Report output layout

## `/app/output/compliance.json`

| Field | Type | Description |
|-------|------|-------------|
| `batch_id` | string | Batch identifier passed to `arcctl report` |
| `summary` | object | Batch-level counters (see below) |
| `records` | array | One object per collection; same field set as `linked.json` records |

### `summary` fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Number of collections in the batch |
| `fully_linked` | integer | Collections meeting fully-linked criteria (see handbook §23.5 for optional geographic linking) |
| `accession_pass` | integer | Collections with `accession_valid` true |
| `accession_fail` | integer | Collections with `accession_valid` false |
| `unresolved_count` | integer | Collections still missing required authority links |

### `records[]` fields

Each compliance record mirrors the corresponding `linked.json` row for:

`collection_id`, `creator_primary`, `subject_headings`, `place_names`, `accession_candidate`, `accession_valid`, `geo_heading_count`

The compliance bundle must include every batch collection even when fully linked. See handbook §23.4.

## `/app/output/unresolved.jsonl`

One JSON object per line for collections still missing required links. Each line includes `collection_id`. Empty file when `summary.unresolved_count` is zero.

Linked record schema: `/app/docs/linked_layout.md`.
