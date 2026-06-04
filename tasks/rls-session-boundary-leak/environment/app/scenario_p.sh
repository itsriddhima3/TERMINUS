#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_reader -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '3';
PREPARE stmt_reader AS SELECT label FROM ledger WHERE active ORDER BY label;
EXECUTE stmt_reader;
\echo ---SWITCH---
SET app.scope_id = '1';
EXECUTE stmt_reader;
DEALLOCATE stmt_reader;
SQL
)"

parse_switch_block "$rows" "acme"
