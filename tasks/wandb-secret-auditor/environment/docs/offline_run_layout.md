Offline run directory layout used by this repo:

- Each run is a directory under `/app/fixtures/` (e.g. `/app/fixtures/run_alpha/`).
- `meta.json`: minimal run metadata (`id`, `project`, `started_at`).
- `logs/`: text logs captured during the run. Common relative paths include `/logs/stdout.txt` and nested files such as `/logs/nested/trace.log`.
- `artifacts/`: binary or text blobs the run produced.
- `links/refs.txt`: one reference per line (some are intentionally malformed).
- `approvals/`: JSON files containing review approvals for the run.

The auditor is expected to walk these directories read-only and produce a report summarizing findings per run.

See also `/app/docs/audit_signal_lexicon.md` for exposure snippet markers and per-line alert granularity expectations.

