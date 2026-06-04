#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '2';
PREPARE stmt_view AS SELECT label FROM active_orders ORDER BY label;
EXECUTE stmt_view;
\echo ---SWITCH---
SET app.scope_id = '1';
EXECUTE stmt_view;
DEALLOCATE stmt_view;
SQL
)"

parse_switch_block "$rows" "acme"
