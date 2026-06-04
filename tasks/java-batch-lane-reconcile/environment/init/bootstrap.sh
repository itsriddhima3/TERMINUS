#!/usr/bin/env bash
set -euo pipefail
export PGUSER="${POSTGRES_USER:-postgres}"
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
mkdir -p /app/output
chmod 777 /app/output
bash /app/init/post_boot.sh
