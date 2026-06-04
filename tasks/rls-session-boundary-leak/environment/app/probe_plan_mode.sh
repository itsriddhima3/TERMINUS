#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh

psql_as_runner -At <<'SQL'
SHOW plan_cache_mode;
SQL
