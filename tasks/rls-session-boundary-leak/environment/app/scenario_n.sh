#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

rows="$(psql_as_runner -At <<'SQL'
SET plan_cache_mode = force_generic_plan;
SET app.scope_id = '1';
PREPARE stmt_union AS
  SELECT label AS row_key FROM ledger WHERE active
  UNION ALL
  SELECT name AS row_key FROM contacts
  ORDER BY row_key;
EXECUTE stmt_union;
\echo ---SWITCH---
SET app.scope_id = '2';
EXECUTE stmt_union;
DEALLOCATE stmt_union;
SQL
)"

python3 - <<'PY' "$rows"
import json, sys
raw = sys.argv[1]
noise = {
    "SET", "PREPARE", "EXECUTE", "DEALLOCATE", "BEGIN", "COMMIT", "ROLLBACK",
    "SAVEPOINT", "RELEASE",
}
if "---SWITCH---" in raw:
    block = raw.split("---SWITCH---", 1)[1]
else:
    block = raw
tokens = [
    line.strip()
    for line in block.splitlines()
    if line.strip() and line.strip() not in noise and not line.strip().startswith("---")
]
allowed = {"beta-lane-a", "beta-lane-b", "Ella Voss"}
foreign = [tok for tok in tokens if tok not in allowed]
print(json.dumps({
    "cross_scope_visible": bool(foreign),
    "foreign_labels_seen": foreign,
    "owned_row_count": len(tokens),
}))
PY
