Our Go sealing pipeline handles Apache Superset export bundles before they leave staging. Sealed drops still carry nested provider and replica-cluster credentials, bundle verify stays green under ciphertext swaps and cross-member relocations, metadata drift bytes do not fail relay checks, and round-trip restore diverges from source fixture bytes on array-heavy exports.

Run `/app/scripts/vault_audit.sh` to produce `/app/output/vault_report.json`. The script rebuilds `/app/bin/vaultctl` from `/app/cmd/vaultctl` using the 32-byte key at `/app/keys/test_master.key`. Fixture paths and needle catalog live in `/app/data/fixture_catalog.json`; scenario bands in `/app/data/scenario_matrix.json`; export layout and report field names in `/app/docs/export_format.md`.

The report uses `schema_version` and a `scenarios` map keyed like the matrix. The audit exits zero only when every scenario row meets its matrix band.
