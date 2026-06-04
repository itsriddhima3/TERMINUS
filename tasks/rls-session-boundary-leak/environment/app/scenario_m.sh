#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_audit AS
  SELECT event_code || ':' || org_ref::text
  FROM audit_log
  ORDER BY org_ref;
EXECUTE stmt_audit;
\echo ---SWITCH---
SET app.scope_id = '2';
EXECUTE stmt_audit;
DEALLOCATE stmt_audit;
SQL
)"

parse_switch_tokens "$rows" "ingest:2"
