#!/usr/bin/env bash
set -euo pipefail
API_BASE="http://127.0.0.1:8080"

api_post_batch() {
  local label="$1"
  local body="$2"
  curl -fsS -X POST "${API_BASE}/api/partition/${label}/batch"     -H 'Content-Type: application/json'     -d "${body}"
}

api_snapshot() {
  local label="$1"
  curl -fsS "${API_BASE}/api/partition/${label}/snapshot"
}

api_reset() {
  curl -fsS -X POST "${API_BASE}/api/admin/reset" >/dev/null || true
}
