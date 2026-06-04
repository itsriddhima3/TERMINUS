#!/usr/bin/env bash
# /app/app/probe_status.sh — quick JSON status probe for CI smoke checks.
set -euo pipefail

export PATH="/app/bin:${PATH}"

bash /app/scripts/init_workspace.sh

if [ ! -x /app/bin/fluxctl ]; then
  bash /app/scripts/build.sh
fi

/app/bin/fluxctl init --scenario SCN-Alpha
/app/bin/fluxctl status --json

SEED="/app/data/seeds/SCN-Alpha.toml"
if [ -f "$SEED" ]; then
  echo "seed_preview=$SEED"
fi
