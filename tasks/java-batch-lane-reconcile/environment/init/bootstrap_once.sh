#!/usr/bin/env bash
set -euo pipefail
FLAG=/var/lib/postgresql/lane_bootstrapped
if [[ -f "$FLAG" ]]; then
  exit 0
fi
bash /app/init/bootstrap.sh
touch "$FLAG"
