#!/usr/bin/env bash
set -euo pipefail

if [[ -f /app/init/.bootstrapped ]]; then
  exit 0
fi

/app/init/bootstrap.sh
touch /app/init/.bootstrapped
