#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_nested AS
  SELECT l.label
  FROM ledger l
  WHERE l.active
    AND EXISTS (
      SELECT 1
      FROM contacts c
      WHERE c.org_ref = l.org_ref
    )
  ORDER BY l.label;
EXECUTE stmt_nested;
\echo ---SWITCH---
SET app.scope_id = '2';
EXECUTE stmt_nested;
DEALLOCATE stmt_nested;
SQL
)"

parse_switch_block "$rows" "beta"
