#!/usr/bin/env bash
set -euo pipefail

PGUSER="${POSTGRES_USER:-postgres}"
PGDATABASE="${POSTGRES_DB:-logistics_db}"

for _ in $(seq 1 180); do
  if psql -U "$PGUSER" -d "$PGDATABASE" -c 'SELECT 1' >/dev/null 2>&1 \
    && psql -U "$PGUSER" -d "$PGDATABASE" -t -A -c \
      "SELECT to_regclass('public.bridge_facility_zone') IS NOT NULL" 2>/dev/null | grep -qx t; then
    exit 0
  fi
  sleep 1
done

echo "logistics_db schema not ready" >&2
exit 1
