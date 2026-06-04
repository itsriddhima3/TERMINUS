#!/usr/bin/env bash
set -euo pipefail

export PGUSER="${POSTGRES_USER:-postgres}"
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
export PGDATABASE="${POSTGRES_DB:-saas_db}"

psql -v ON_ERROR_STOP=1 <<'SQL'
GRANT USAGE ON SCHEMA public TO svc_runner, svc_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO svc_runner, svc_reader;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO svc_runner, svc_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO svc_runner, svc_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO svc_runner, svc_reader;
SQL

mkdir -p /app/output
chmod 777 /app/output
