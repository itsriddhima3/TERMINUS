#!/usr/bin/env bash
set -euo pipefail

/usr/local/bin/docker-entrypoint.sh postgres &
until pg_isready -U "${POSTGRES_USER:-postgres}" -q; do
  sleep 0.2
done

exec "$@"
