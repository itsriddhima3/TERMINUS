#!/usr/bin/env bash
set -euo pipefail
wait_for_pg() {
  local tries=150
  while (( tries > 0 )); do
    if pg_isready -U "${POSTGRES_USER:-postgres}" -q 2>/dev/null; then
      if psql -U "${POSTGRES_USER:-postgres}" -d postgres -At -c "SELECT 1" >/dev/null 2>&1; then
        return 0
      fi
    fi
    sleep 0.2
    tries=$((tries - 1))
  done
  return 1
}
wait_for_pg
bash /app/init/bootstrap_once.sh
