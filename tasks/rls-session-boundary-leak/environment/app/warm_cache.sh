#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh

psql_as_runner <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE warm_ledger AS SELECT label FROM ledger WHERE active ORDER BY label;
EXECUTE warm_ledger;
EXECUTE warm_ledger;
DEALLOCATE warm_ledger;
SQL
