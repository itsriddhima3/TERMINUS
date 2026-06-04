#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '2';
PREPARE stmt_win AS
  SELECT label
  FROM (
    SELECT label, row_number() OVER (ORDER BY label) AS rn
    FROM ledger
    WHERE active
  ) ranked
  WHERE rn <= 10
  ORDER BY label;
EXECUTE stmt_win;
\echo ---SWITCH---
SET app.scope_id = '1';
EXECUTE stmt_win;
DEALLOCATE stmt_win;
SQL
)"

parse_switch_block "$rows" "acme"
