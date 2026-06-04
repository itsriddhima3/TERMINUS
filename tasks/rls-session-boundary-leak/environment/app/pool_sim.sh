#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh

target_scope="$1"
shift

psql_as_runner <<SQL
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE pool_stmt AS SELECT label FROM ledger WHERE active ORDER BY label;
EXECUTE pool_stmt;
SET app.scope_id = '2';
EXECUTE pool_stmt;
SET app.scope_id = '${target_scope}';
EXECUTE pool_stmt;
DEALLOCATE pool_stmt;
SQL
