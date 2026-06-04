#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_cte AS
  WITH scoped AS (
    SELECT label
    FROM ledger
    WHERE active
  )
  SELECT label FROM scoped ORDER BY label;
EXECUTE stmt_cte;
\echo ---SWITCH---
SET app.scope_id = '3';
EXECUTE stmt_cte;
DEALLOCATE stmt_cte;
SQL
)"

parse_switch_block "$rows" "delta"
