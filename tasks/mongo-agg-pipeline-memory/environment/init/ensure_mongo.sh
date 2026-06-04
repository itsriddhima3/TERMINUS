#!/usr/bin/env bash
set -euo pipefail

for _ in $(seq 1 60); do
  if mongosh --quiet --eval 'db.runCommand({ ping: 1 })' >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.3
done
echo "mongo not ready" >&2
exit 1
