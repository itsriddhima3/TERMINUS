# Assembly line PLC log layout

Each station keeps `meta.json` (replication lag, commit watermark) and one or more PLC segment files (`cache_001.jsonl` or legacy `seg_001.jsonl`). The active bundle under `data/active/` lists quorum size, split generation, jitter tight band, and trust anchor for origin stamp checks. Grading harness packs live under `/tests/fixtures/` and are copied into `/app/data/active/` before verification runs.
