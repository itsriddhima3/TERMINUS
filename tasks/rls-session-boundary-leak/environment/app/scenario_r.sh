#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

/app/app/warm_cache.sh >/dev/null

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE warm_stmt AS SELECT label FROM ledger WHERE active ORDER BY label;
EXECUTE warm_stmt;
\echo ---SWITCH---
SET app.scope_id = '3';
EXECUTE warm_stmt;
DEALLOCATE warm_stmt;
SQL
)"

parse_switch_block "$rows" "delta"
