#!/bin/bash
set -euo pipefail

HEALTH_URL="http://127.0.0.1:8080/health"

if [ -f /app/var/api.pid ] && kill -0 "$(cat /app/var/api.pid)" 2>/dev/null; then
  if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    exit 0
  fi
  kill "$(cat /app/var/api.pid)" 2>/dev/null || true
  rm -f /app/var/api.pid
fi

php -S 127.0.0.1:8080 -t /app/api/public /app/api/public/index.php \
  >/app/var/api.log 2>&1 &
echo $! >/app/var/api.pid

for _ in $(seq 1 50); do
  if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.2
done

echo "API did not become ready at $HEALTH_URL" >&2
exit 1
