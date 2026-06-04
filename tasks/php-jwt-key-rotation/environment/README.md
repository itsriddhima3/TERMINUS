# Vault edge service

Local PHP API on `127.0.0.1:8080` backed by SQLite at `/app/var/vault.db`.
Operator CLI lives under `/app/cli` (`guardctl` wrapper).

Start API: `bash /app/scripts/start-api.sh`
Initialize empty DB: `bash /app/scripts/init-db.sh`

See `/app/docs/api_notes.md` and `/app/docs/schema_digest.md` for wire and persistence notes.
