# SQLite layout (`/app/var/vault.db`)

## signing_keys
- `kid` (TEXT, PK)
- `public_pem` (TEXT)
- `private_pem` (TEXT, nullable for retired material)
- `status` (TEXT) — exactly one row `active`, at most one `previous`, others `retired`
- `created_at` (TEXT, ISO-8601 UTC)

## users
- `id`, `username`, `pass_hash`

## audit_log
- `id`, `event_type`, `kid`, `detail_json`, `created_at`

Rotation events use `event_type` values `key_retired` then `key_promoted` (retired detail links successor kid; promoted detail links prior kid).

Pre-rotation there is a single active signing key. JWKS publishes active material only until rotation introduces a previous kid for grace verification.
