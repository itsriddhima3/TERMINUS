#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '2';
PREPARE stmt_lat AS
  SELECT l.label
  FROM ledger l
  CROSS JOIN LATERAL (
    SELECT c.name
    FROM contacts c
    WHERE c.org_ref = l.org_ref
    LIMIT 1
  ) probe
  WHERE l.active
  ORDER BY l.label;
EXECUTE stmt_lat;
\echo ---SWITCH---
SET app.scope_id = '1';
EXECUTE stmt_lat;
DEALLOCATE stmt_lat;
SQL
)"

parse_switch_block "$rows" "acme"
