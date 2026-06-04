#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '2';
PREPARE stmt_inv AS SELECT sku FROM inventory ORDER BY sku;
EXECUTE stmt_inv;
\echo ---SWITCH---
SET app.scope_id = '1';
EXECUTE stmt_inv;
DEALLOCATE stmt_inv;
SQL
)"

parse_switch_tokens "$rows" "CR-"
