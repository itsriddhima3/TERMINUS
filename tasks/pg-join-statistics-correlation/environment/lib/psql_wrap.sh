#!/usr/bin/env bash
set -euo pipefail

export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGDATABASE="${PGDATABASE:-logistics_db}"

psql_as_planner() {
  PGUSER=svc_planner PGPASSWORD=planner_pass psql -v ON_ERROR_STOP=1 "$@"
}
