#!/usr/bin/env bash
set -euo pipefail

PGADMIN_DB=postgres

ensure_app_database() {
  local db="${POSTGRES_DB:-saas_db}"
  if psql -U "${POSTGRES_USER:-postgres}" -d "${PGADMIN_DB}" -tc "SELECT 1 FROM pg_database WHERE datname = '${db}'" 2>/dev/null | grep -q 1; then
    return 0
  fi
  psql -U "${POSTGRES_USER:-postgres}" -d "${PGADMIN_DB}" -c "CREATE DATABASE \"${db}\"" >/dev/null 2>&1 || true
}

bootstrap_once() {
  local marker="/var/lib/postgresql/data/.tb_bootstrapped"
  local lock="/var/lib/postgresql/data/.tb_bootstrap.lock"

  exec 200>"${lock}"
  flock -x 200

  ensure_app_database

  if [[ -f "${marker}" ]]; then
    return 0
  fi

  if psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-saas_db}" -tc "SELECT to_regclass('public.org_dim')" | grep -q org_dim; then
    touch "${marker}"
    return 0
  fi

  /app/init/bootstrap.sh
  touch "${marker}"
}
