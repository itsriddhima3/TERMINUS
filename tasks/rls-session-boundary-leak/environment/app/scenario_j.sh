#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_agg AS
  SELECT count(*)::integer
  FROM ledger
  WHERE active;
EXECUTE stmt_agg;
\echo ---SWITCH---
SET app.scope_id = '2';
EXECUTE stmt_agg;
DEALLOCATE stmt_agg;
SQL
)"

parse_switch_count "$rows" 2
