#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh

set_scope() {
  local scope_id="$1"
  psql_as_runner -c "SET app.scope_id = '${scope_id}';"
}

reset_session() {
  psql_as_runner -c "DISCARD ALL;"
}
