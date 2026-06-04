#!/usr/bin/env bash
set -euo pipefail

export PGHOST="${PGHOST:-127.0.0.1}"
export PGPORT="${PGPORT:-5432}"
export PGDATABASE="${PGDATABASE:-saas_db}"

psql_as_runner() {
  PGUSER=svc_runner PGPASSWORD=runner_pass psql -v ON_ERROR_STOP=1 "$@"
}

psql_as_reader() {
  PGUSER=svc_reader PGPASSWORD=reader_pass psql -v ON_ERROR_STOP=1 "$@"
}
