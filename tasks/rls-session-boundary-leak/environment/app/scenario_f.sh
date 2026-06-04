#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_batch AS SELECT label FROM ledger WHERE active ORDER BY label;
EXECUTE stmt_batch;
EXECUTE stmt_batch;
\echo ---SWITCH---
SET app.scope_id = '2';
EXECUTE stmt_batch;
DEALLOCATE stmt_batch;
SQL
)"

parse_switch_block "$rows" "beta"
