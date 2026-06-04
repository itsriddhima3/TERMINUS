# Smart-meter NDJSON reconciliation bench

Java CLI (`/app/bin/meterctl`) plus a local Spring Boot reference service on `http://127.0.0.1:8080`.
Device and tariff catalogs live under `/app/data/`. Intermediate artifacts use `/app/var/`; reconciliation output lands in `/app/output/`.

See `/app/docs/` for NDJSON stream pagination, interval gap rules, tariff windows, and delta checks.
