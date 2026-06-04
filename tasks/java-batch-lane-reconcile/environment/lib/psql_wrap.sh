#!/usr/bin/env bash
set -euo pipefail
psql_lane() {
  psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-lane_db}" -v ON_ERROR_STOP=1 "$@"
}
