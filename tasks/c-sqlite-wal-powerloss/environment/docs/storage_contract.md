# Storage contract

Flash-resident catalogs use write-ahead logging mode. Readers expect `schema_marker` 2 in the meta table. Ingest loads kit-labeled rows from CSV seeds under `/app/data/seeds/`.

## Recovery report (`/app/output/recovery_report.json`)

JSON object with:

- `scenarios`: array of per-crash-suite results stored under `/tmp/datalog_audit/` as `{id}.db` (for example `/tmp/datalog_audit/alpha.db`, `/tmp/datalog_audit/bravo.db`, `/tmp/datalog_audit/charlie.db`, `/tmp/datalog_audit/delta.db`). Each entry includes `id`, `kit`, `recovered`, `integrity_ok`, `row_count`, and `schema_marker`.
- Successful maintenance writes `/tmp/datalog_audit/.cycle_sync_marker`.
- `summary`: object with `all_recovered` (boolean) and `audit_digest` (hex string).

Row totals after recovery must match `/app/docs/field_matrix.md` for each kit. A passing run shows every scenario `recovered` and `integrity_ok`, with `schema_marker` 2 (see meta table), and `summary.all_recovered` true. `PRAGMA integrity_check` on each reopened catalog must return the literal string `ok`.

Field firmware bindings in `/app/config/bench_profiles.toml` define K2, P8, and Q1 class requirements reconciled by `/app/scripts/cycle_diag.sh`.

Reopened catalogs must report `PRAGMA synchronous` value `2` (FULL) and `PRAGMA journal_mode` value `wal`. After a clean maintenance cycle the main catalog must not retain a `-wal` or `-shm` sidecar with non-zero length; probe catalogs named `{id}_probe.db` under `/tmp/datalog_audit/` follow the same rule. The meta table holds exactly one `schema_marker` row with value `2`. The cycle sync marker file must be non-empty.

Seed loads preserve contiguous `seq` values from 1 through each kit row total in the matrix, with `val = seq * 1.70` for every reading row.
