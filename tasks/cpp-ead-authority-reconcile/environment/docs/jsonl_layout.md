# Parse JSONL layout

Output file: `/app/var/records.jsonl`

One JSON object per line (one finding aid per line in batch `ARC-2024-Q2`).

## Record fields

| Field | Type | Description |
|-------|------|-------------|
| `collection_id` | string | Collection identifier from the finding aid |
| `title` | string | `<unittitle>` text for the collection |
| `date_span` | string | Normalized `<unitdate>` range (hyphen wire form, century digits preserved) |
| `creators` | array | All `<name>` entries from `<controlaccess>`, in document order |

## `creators` entries

Each element is an object:

- `type`: `"corp"` for `<corpname>`, `"pers"` for `<persname>`
- `name`: normalized display string from the EAD name node

When a finding aid lists both a corporate body and a personal name in the same `<controlaccess>` block, the corporate entry must appear before the personal entry in the `creators` array.

Companion CSV: `/app/docs/csv_layout.md`.
