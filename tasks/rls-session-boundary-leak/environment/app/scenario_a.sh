#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh
source /app/lib/scenario_parse.sh

run_adhoc_single() {
  local scope_id="$1"
  local expected_prefix="$2"
  local rows
  rows="$(psql_as_runner -At <<SQL
SET app.scope_id = '${scope_id}';
SELECT label FROM ledger WHERE active ORDER BY label;
SQL
)"
  python3 - <<'PY' "$rows" "$expected_prefix"
import json, sys
rows, prefix = sys.argv[1], sys.argv[2]
noise = {
    "SET", "PREPARE", "EXECUTE", "DEALLOCATE", "BEGIN", "COMMIT", "ROLLBACK",
    "SAVEPOINT", "RELEASE",
}
labels = [
    line.strip()
    for line in rows.splitlines()
    if line.strip() and line.strip() not in noise
]
foreign = [label for label in labels if not label.startswith(prefix)]
print(json.dumps({
    "cross_scope_visible": bool(foreign),
    "foreign_labels_seen": foreign,
    "owned_row_count": len(labels),
}))
PY
}

run_adhoc_single 1 "acme"
run_adhoc_single 2 "beta"
run_adhoc_single 3 "delta"
