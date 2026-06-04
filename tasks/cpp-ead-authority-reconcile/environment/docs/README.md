# Archives reconciliation workspace

Batch-driven EAD ingest runs through `arcctl` (`parse`, `link`, `report`) against the local authority API on port 3000. Batch membership is listed in `/app/config/batch_registry.json`. Runtime paths are in `/app/config/run.toml`.

See `api_contract.md`, `csv_layout.md`, and `bench_precedence.md` for interface notes.
