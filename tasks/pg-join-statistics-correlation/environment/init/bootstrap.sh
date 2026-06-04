#!/usr/bin/env bash
set -euo pipefail

export PGUSER="${POSTGRES_USER:-postgres}"
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
export PGDATABASE="${POSTGRES_DB:-logistics_db}"

apply_sql() {
  psql -v ON_ERROR_STOP=1 -f "$1"
}

apply_sql /app/store/001_extensions.sql
apply_sql /app/store/002_core_tables.sql
apply_sql /app/store/003_indexes.sql
apply_sql /app/q/m3_helpers.sql
apply_sql /app/store/a7k.sql

for file in /app/migrations/x9k.sql /app/migrations/v1_marker.sql /app/migrations/v2_stats_note.sql /app/migrations/w9_decoy.sql; do
  apply_sql "$file"
done

apply_sql /app/lib/r2k.sql

apply_sql /app/store/004_grants.sql
apply_sql /app/store/900_seed_data.sql

for file in /app/v/*.sql; do
  apply_sql "$file"
done

for file in /app/q/workload_spine.sql; do
  apply_sql "$file"
done

psql -v ON_ERROR_STOP=1 -c "ANALYZE;"

/app/init/post_boot.sh
