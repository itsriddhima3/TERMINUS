#!/bin/bash
set -euo pipefail

DB=/app/service/db/ratings.db
mkdir -p /app/service/db /app/output/splits /app/output/model /app/output/submission /app/var
if [ ! -f "$DB" ]; then
  sqlite3 "$DB" < /app/service/db/schema.sql
  sqlite3 "$DB" < /app/service/db/seeds.sql
fi

if ! pgrep -f "rackup" >/dev/null 2>&1; then
  nohup rackup -o 0.0.0.0 -p 4567 /app/service/config.ru >/app/var/rack.log 2>&1 &
  sleep 1
fi
