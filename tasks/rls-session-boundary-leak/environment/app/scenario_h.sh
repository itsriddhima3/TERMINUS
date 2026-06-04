#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
BEGIN;
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_save AS SELECT label FROM ledger WHERE active ORDER BY label;
EXECUTE stmt_save;
SAVEPOINT iso_sp;
SET app.scope_id = '3';
EXECUTE stmt_save;
ROLLBACK TO SAVEPOINT iso_sp;
\echo ---SWITCH---
SET app.scope_id = '2';
EXECUTE stmt_save;
DEALLOCATE stmt_save;
COMMIT;
SQL
)"

parse_switch_block "$rows" "beta"
