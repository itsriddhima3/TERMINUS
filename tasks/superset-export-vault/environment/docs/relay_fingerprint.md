# Relay fingerprint policy

Manifest member fingerprints are produced by `fold_r2` in the ledger package. Staging builds historically normalized metadata member bytes (line trimming before hashing) so diff-friendly YAML compared cleanly in review tools. Production relay policy expects **raw member bytes** as stored in the tarball.

`FoldCanonical` computes a straight SHA-256 over untouched payload bytes and is referenced by logging helpers. Only `RelayH4` feeds the manifest.

## Verify tiers

`GateF8` compares relay fingerprints member-by-member. **Metadata-class members** (`metadata/*.yaml`, `metadata/*.json`) are on a deferred relay tier in the staging profile: their fingerprints are recorded in the manifest but not re-checked during bundle verify. Non-metadata members (`charts/`, `datasets/`, …) are checked on every verify pass.

`GateZ1` walks the envelope table and must reopen each sealed field against the active 32-byte master key.
