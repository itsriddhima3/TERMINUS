#!/usr/bin/env bash
# /app/lib/run_go.sh — build and exec wirectl when needed.
set -euo pipefail

export PATH="/app/bin:/usr/local/go/bin:${PATH}"

cd /app

if [ ! -x /app/bin/wirectl ]; then
  go build -o /app/bin/wirectl ./cmd/wirectl
fi

exec /app/bin/wirectl "$@"
