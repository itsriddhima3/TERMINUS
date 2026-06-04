Our Spring Boot chunk ingest service at `/app` loses rows and duplicates business keys when we run parallel uploads on North-Shelf (six active slots), East-Crate (ten), or West-Bin (four). Single-threaded replays on those families still look fine.

Run `/app/app/lane_audit.sh` to populate `/app/output/lane_audit.json`. That JSON carries schema_version, catalog_partitions, scenarios, lost_rows, duplicate_external_keys, unstable_totals, ingest_compliance, and stress_summary. Reconcile the facility so concurrent audits show no row loss, no key collisions, stable rollup totals, and ingest compliance across every matrix row.

The playbooks under `/app/docs/` blame database tuning, but QA thinks we are breaking several invariants at once. If the boundary material under `/app/docs/boundary_contract/` disagrees with a playbook, follow the boundary spec; `/app/docs/bench_precedence.md` says how to resolve that conflict.
