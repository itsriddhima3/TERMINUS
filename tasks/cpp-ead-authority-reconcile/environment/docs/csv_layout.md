# Parse CSV layout

Output file: `/app/var/records.csv`

Column order:

`collection_id,title,date_span,creator_primary,subject_headings,place_names`

- `subject_headings` and `place_names` are semicolon-separated raw heading text at parse time.
- Companion JSONL: `/app/var/records.jsonl` (one record object per line).
