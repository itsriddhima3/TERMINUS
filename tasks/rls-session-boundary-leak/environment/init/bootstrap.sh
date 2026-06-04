#!/usr/bin/env bash
set -euo pipefail

export PGUSER="${POSTGRES_USER:-postgres}"
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
export PGDATABASE="${POSTGRES_DB:-saas_db}"

apply_sql() {
  local file="$1"
  psql -v ON_ERROR_STOP=1 -f "$file"
}

apply_sql /app/store/001_extensions.sql
apply_sql /app/store/002_types.sql
apply_sql /app/store/003_core_tables.sql
apply_sql /app/store/004_indexes.sql
apply_sql /app/store/005_rls_enable.sql

apply_sql /app/q/x7q.sql
apply_sql /app/q/m2p.sql
apply_sql /app/q/m3_helpers.sql
apply_sql /app/q/p9_scope.sql

for file in /app/v/*.sql; do
  apply_sql "$file"
done

apply_sql /app/store/007_grants.sql
apply_sql /app/store/008_seed_data.sql
apply_sql /app/store/009_event_hooks.sql
apply_sql /app/store/audit_scalar.sql

for file in /app/views/*.sql; do
  apply_sql "$file"
done

for file in /app/migrations/*.sql; do
  apply_sql "$file"
done

/app/init/post_boot.sh
