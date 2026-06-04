#!/bin/bash
set -euo pipefail
if curl -sf "http://127.0.0.1:3000/health" >/dev/null 2>&1; then
  exit 0
fi
nohup node /app/api/server.js --port 3000 --host 127.0.0.1 >/tmp/arc-api.log 2>&1 &
for _ in $(seq 1 50); do
  if curl -sf "http://127.0.0.1:3000/health" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.1
done
echo "arc authority api failed to start" >&2
exit 1
