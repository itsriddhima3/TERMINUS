# Customs reconciliation bench workspace

Java CLI (`/app/bin/customsctl`) plus a local Fastify reference service on port 3921.
Shipment CSV batches live under `/app/data/shipments/`. Intermediate artifacts use `/app/var/`; reconciliation output lands in `/app/output/`.

See `/app/docs/` for CSV layout, HS folding rules, API shapes, and duty math notes.
