# Catalog part 01 — K2 open bundle

Field units bind catalog handles through the **K2** gate-layer open bundle before any ingest burst. Bench class-0 sync bindings are valid only on the lab harness; deployed firmware must honor **field_sync_class = 2** from `/app/config/bench_profiles.toml` plus the auxiliary barrier named there.

Relaxed open profiles let frames reach flash without the ordering guarantees the compaction window assumes. After an abrupt stop, readers may still see an intact main file yet fail layout checks because K2 never committed the frame metadata the cycle driver expects.

The meta table carries `schema_marker` 2 for active firmware. K2 does not create layout — it only governs how handles accept commits before P8 runs.
