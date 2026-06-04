#!/usr/bin/env bash
# Emits dimension hints from the last stress workdir — diagnostics only.
set -euo pipefail

ROOT="${1:-/tmp/m7desk_stress}"
if [[ ! -d "$ROOT" ]]; then
  echo "probe: no work root at $ROOT"
  exit 0
fi

for db in "$ROOT"/*.db; do
  [[ -f "$db" ]] || continue
  name="$(basename "$db" .db)"
  journal="$(sqlite3 "$db" 'PRAGMA journal_mode;')"
  sync="$(sqlite3 "$db" 'PRAGMA synchronous;')"
  busy="$(sqlite3 "$db" "SELECT value FROM meta WHERE key='busy_events';" 2>/dev/null || echo -1)"
  rows="$(sqlite3 "$db" 'SELECT COUNT(*) FROM facts;')"
  echo "probe scenario=$name journal=$journal sync=$sync busy_meta=$busy fact_rows=$rows"
done
