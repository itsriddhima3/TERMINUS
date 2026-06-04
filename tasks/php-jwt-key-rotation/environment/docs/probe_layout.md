# Probe and digest layout (CLI map/verify helpers)

## Service map digests

- schema_fingerprint: SHA-256 hex over sorted fragments `table:col1,col2,...` joined by `|`.
- active_pubkey_digest: SHA-256 hex of the active row public_pem bytes.
- jwks_bundle_digest: SHA-256 hex of the JWKS `keys` JSON array (compact separators).

## Access report matrix

- fixture_order follows `/app/platform/runtime.json` fixture_cases order.
- matrix_digest hashes tuples of case_id, accepted, local_ok, api_ok, crypto_ok, http_status per row.

## Rotation audit

- audit_sequence_ok requires key_retired before key_promoted in audit_log order.
- jwks_kids must match live `/.well-known/jwks.json` after rotation (previous + active).
- signing_key_row_count is 2 with exactly one active and one previous row.
