#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_reuse AS SELECT label FROM ledger WHERE active ORDER BY label;
EXECUTE stmt_reuse;
\echo ---SWITCH---
SET app.scope_id = '2';
EXECUTE stmt_reuse;
DEALLOCATE stmt_reuse;
SQL
)"

parse_switch_block "$rows" "beta"
