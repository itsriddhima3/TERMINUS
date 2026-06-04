#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_join AS
  SELECT l.label
  FROM ledger l
  JOIN contacts c ON c.org_ref = l.org_ref
  WHERE l.active
  ORDER BY l.label;
EXECUTE stmt_join;
\echo ---SWITCH---
SET app.scope_id = '3';
EXECUTE stmt_join;
DEALLOCATE stmt_join;
SQL
)"

parse_switch_block "$rows" "delta"
