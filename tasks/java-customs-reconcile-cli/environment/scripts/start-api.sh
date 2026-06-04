#!/bin/bash
set -euo pipefail
if curl -sf "http://127.0.0.1:3921/health" >/dev/null 2>&1; then
  exit 0
fi
nohup node /app/api/server.js --port 3921 --host 127.0.0.1 >/tmp/customs-api.log 2>&1 &
for _ in $(seq 1 50); do
  if curl -sf "http://127.0.0.1:3921/health" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.1
done
echo "customs api failed to start" >&2
exit 1
