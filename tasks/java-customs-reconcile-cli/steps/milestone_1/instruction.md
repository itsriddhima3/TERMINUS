Start `/app/scripts/start-api.sh`, then use `/app/bin/customsctl` against shipment CSV batches under `/app/data/shipments/`.

`customsctl ingest SHIP-2024-Q1` should persist `/app/var/shipments.json` with top-level `batch_id` and a `lines` array. Each line must carry exactly six fields from the shipment CSV — `line_id`, `importer_id`, `hs10`, `currency`, `declared_value`, and `declared_duty` — with `hs10` and `currency` normalized from the raw columns. The on-disk file does not match that contract today: line order can be reversed, dotted HS tokens collapse to the wrong `hs10` width, and currency aliases like `eur` may not land as the ISO tags the reference service expects. HTTP health on port 3921 can still return 200.

Reconcile ingest so a fresh run reproduces six lines in catalog order with ten-digit `hs10` values and normalized `currency` fields. Notes under `/app/docs/` disagree on HS width and currency annex rules — use `/app/docs/bench_precedence.md` to decide which note wins (dotted `8471.30.00` should fold to `8471300000`).

When you're done, **signal completion** and include the command you used to regenerate the manifest.
