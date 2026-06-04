# Shipment CSV layout

Each batch file under `/app/data/shipments/<batch-id>.csv` uses a header row:

`line_id,importer_id,hs_raw,currency_raw,declared_value,declared_duty`

Ingest preserves file order (L001 first). Persisted JSON uses keys `batch_id` and `lines` with per-line `hs10` and `currency` after normalization.
