# Catalog part 01 — K2 open dimension

K2 runs inside the `k9m` crate root before the Q3 dimension acquires handles.

Authoritative numbers live under `[m7]` in `/app/config/bench_profiles.toml`:

- `journal_family_required` must be the effective family after **all** pragma batches on the handle complete (sqlite applies pragmas in order; a later batch may change the family).
- `min_busy_wait_ms` is the minimum `busy_timeout` value in milliseconds.
- `synchronous_mode_required` is the integer sqlite reports for `PRAGMA synchronous` (1 means NORMAL in the stock build).
- `wal_autocheckpoint_pages` must be set when the family is write-ahead.
- When `forbid_downgrade_pragma_sequence` is true, no follow-up batch may move the family away from the required value.

Stress ledgers that show a non-wal `journal_mode` while catalogs contain rows usually mean K2 did not finish in the effective family, not that Q3 failed first. An on-disk `PRAGMA journal_mode` query that returns `delete` means K2 failed the family requirement even if an earlier source line mentioned write-ahead.
