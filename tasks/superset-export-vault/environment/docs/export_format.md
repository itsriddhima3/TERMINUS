# Export bundle layout

Apache Superset exports arrive as gzip-compressed tar archives. Metadata lives under `metadata/` as YAML or JSON describing database connections and OAuth client registrations. Non-metadata members (`charts/`, `datasets/`, etc.) must pass through sealing unchanged.

Sealed drops add `vault/manifest.json` listing member fingerprints and envelope identifiers for redacted fields.

The audit report at `/app/output/vault_report.json` uses `schema_version`, a `scenarios` map, and per-row fields named in `/app/data/scenario_matrix.json` (`plaintext_hits`, `manifest_ok`, `verify_ok`, `digest_match`, `source_digest`, `restored_digest`, optional `tamper` mode keys).
