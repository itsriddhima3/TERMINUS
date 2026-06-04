#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_triple AS SELECT label FROM ledger WHERE active ORDER BY label;
EXECUTE stmt_triple;
SET app.scope_id = '2';
EXECUTE stmt_triple;
\echo ---SWITCH---
SET app.scope_id = '3';
EXECUTE stmt_triple;
DEALLOCATE stmt_triple;
SQL
)"

parse_switch_block "$rows" "delta"
