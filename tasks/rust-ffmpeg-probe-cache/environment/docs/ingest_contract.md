# Stress ledger contract

`/app/output/stress_ledger.json` is produced by the runtime binary `run-stress` subcommand. Per-lane sqlite catalogs materialize under `/tmp/m7desk_stress` as `{lane_id}.db` files during the harness run. Clip bodies are read from `/app/data/clips` (for example `a01.mp4` on lane A).

## Top-level

- `lanes`: array of per-catalog results
- `summary.all_complete`: true only when every lane meets row and contention requirements
- `summary.ledger_digest`: lowercase hex SHA-256 of the ledger JSON with `ledger_digest` forced to empty string before hashing

## Lane object

| field | type | requirement |
|-------|------|-------------|
| lane_id | string | matches manifest lane_id |
| expected_rows | integer | from lane_matrix |
| observed_rows | integer | `SELECT COUNT(*) FROM facts` on lane catalog |
| busy_events | integer | meta `busy_events` counter; must be 0 after successful stress |
| journal_mode | string | `PRAGMA journal_mode` on catalog; must be `wal` for matrix lanes |
| integrity_ok | boolean | true when `PRAGMA integrity_check` returns `ok` |

## Cross-scenario invariants

- The sum of `SELECT COUNT(*) FROM facts` across all four catalogs under `/tmp/m7desk_stress/` must be **32** (four matrix scenarios × eight clips each).
- Each catalog's `clip_key` values must equal the clip filename list for that scenario in `/app/data/stress_manifest.toml` (no extras, no omissions).
- Within one catalog, all `stream_hash` values must be distinct (one hash per ingested clip body).
- `summary.ledger_digest` must equal the lowercase hex SHA-256 of the on-disk ledger JSON after replacing the `ledger_digest` field value with an empty string (same pretty-printed body the harness hashes before it writes the final digest).
- A successful harness run must not emit `database is locked` on stderr.
- **Repeat-run success:** After a successful first pass, clearing `/tmp/m7desk_stress/` and invoking `run-stress` again with the same manifest must exit **0** with clean stderr (no lock errors). The **lane_b** catalog must again hold the matrix `expected_rows` count in `facts` (re-ingest must not drop rows).
- **WAL checkpoint busy=0:** `PRAGMA wal_checkpoint;` on each matrix catalog under `/tmp/m7desk_stress/` returns a pipe-separated row; the first field (SQLite busy-frames tally) must be **0** — no busy WAL frames remain after ingest.
- Scenario **lane_a** clip `a01.mp4` must persist `dur_ms` equal to the millisecond duration ffprobe reports for that file (rounded half-up from seconds).
- Effective `PRAGMA journal_mode` on each matrix catalog must be `wal`, not `delete` (K2 `journal_family_required`).
- `PRAGMA synchronous` must not be **0** (OFF) on each matrix catalog; after K2 NORMAL is applied, WAL catalogs may report **1** or **2** per `[m7] synchronous_mode_required`.
