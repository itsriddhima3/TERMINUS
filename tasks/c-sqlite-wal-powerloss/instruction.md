Our field telemetry units fail overnight with layout errors after brief power loss during the compaction window. Flash still holds the main catalog file, but readers report layout failures across kit catalogs.

Rebuild `/app/bin/datalog` with `/app/scripts/build.sh` (the `/app` Makefile links gate, maintenance, journal, and util objects — not only trees under `/app/src`). Run `/app/bin/datalog audit --output /app/output/recovery_report.json`.

The audit JSON must match `/app/docs/storage_contract.md` and kit row totals must match `/app/docs/field_matrix.md`. Required report members: `scenarios`, `recovered`, `row_count`, `schema_marker`, `integrity_ok`, `summary.all_recovered`, and `summary.audit_digest`.

Materialized catalogs and probe databases live under `/tmp/datalog_audit/` as specified in the storage contract. Trace failing audit dimensions through `/app/config/bench_profiles.toml`, the catalog memo tree under `/app/docs/catalog/`, and the linked C sources under `/app` that implement those bindings — not decoy preview modules.
