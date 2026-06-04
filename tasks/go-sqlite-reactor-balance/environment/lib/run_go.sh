#!/usr/bin/env bash
# /app/lib/run_go.sh — helper to run fluxctl with CGO enabled.
set -euo pipefail

export CGO_ENABLED=1
export PATH="/app/bin:/usr/local/go/bin:${PATH}"

if [ ! -x /app/bin/fluxctl ]; then
  bash /app/scripts/build.sh
fi

exec /app/bin/fluxctl "$@"
