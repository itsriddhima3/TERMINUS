#!/usr/bin/env bash
set -euo pipefail

/usr/local/bin/docker-entrypoint.sh mongod &
until mongosh --quiet --eval 'db.runCommand({ ping: 1 })' >/dev/null 2>&1; do
  sleep 0.3
done

if [[ ! -f /data/db/.tb_bootstrapped ]]; then
  /app/init/bootstrap.sh
  touch /data/db/.tb_bootstrapped
fi

exec "$@"
