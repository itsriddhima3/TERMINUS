#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh

scope_id="$1"
psql_as_runner -c "SET app.scope_id = '${scope_id}';" >/dev/null
