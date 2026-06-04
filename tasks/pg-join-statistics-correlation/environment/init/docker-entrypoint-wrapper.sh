#!/usr/bin/env bash
set -euo pipefail

/usr/local/bin/docker-entrypoint.sh postgres &
until pg_isready -U "${POSTGRES_USER:-postgres}" -q; do
  sleep 0.2
done

if [[ ! -f /var/lib/postgresql/data/.tb_bootstrapped ]]; then
  for _ in $(seq 1 120); do
    if psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-logistics_db}" -c 'SELECT 1' >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done
  /app/init/bootstrap.sh
  touch /var/lib/postgresql/data/.tb_bootstrapped
fi

exec "$@"
