# Catalog part 02 — Q3 write dimension

Q3 lives in the `r2n` crate root and owns how parallel ingest scopes sqlite handles.

`[q3]` in `/app/config/bench_profiles.toml` defines:

- `pool_max_must_equal_manifest_workers`: the connection pool upper bound must equal the `workers` integer from `/app/data/stress_manifest.toml`, not a hard-coded smaller cap and not `max(2, workers)`.
- `each_insert_in_explicit_transaction`: every fact insert must run inside a `rusqlite::Transaction` that commits before the handle returns to the pool.
- `forbid_process_wide_shared_handle`: a single `Arc<Connection>` shared across rayon workers is out of profile even if crate dependencies list pool crates.

Partial row totals with quiet stderr and near-zero `busy_events` often mean Q3 serialized writers or omitted transaction boundaries, while K2 already shows wal in a one-off manual probe.

The `r2n` crate manifest may list pool libraries; profile compliance is determined by runtime behavior under stress, not by `Cargo.toml` tokens alone.
