# Link output layout

Output file: `/app/output/linked.json`

## Top level

| Field | Type | Description |
|-------|------|-------------|
| `batch_id` | string | Batch identifier passed to `arcctl link` |
| `records` | array | One object per collection in the batch |

## Per-record fields (`records[]`)

| Field | Type | Description |
|-------|------|-------------|
| `collection_id` | string | Collection identifier |
| `creator_primary` | string | Resolved primary creator authority id (corporate body wins when both corp and pers are present) |
| `subject_headings` | string | Resolved subject authority id from the LCSH stem |
| `place_names` | string | Resolved place authority id (empty when no geographic headings were declared) |
| `accession_candidate` | string | Accession string proposed for validation (collection id wire form) |
| `accession_valid` | boolean | Whether the authority service accepted the accession candidate |
| `geo_heading_count` | integer | Count of `<geogname>` elements in the finding aid (zero when none declared) |

Authority resolution behavior: `/app/docs/api_contract.md`. Curator precedence: `/app/docs/bench_precedence.md`.
