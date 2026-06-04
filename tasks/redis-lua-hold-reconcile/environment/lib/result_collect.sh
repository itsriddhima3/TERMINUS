#!/usr/bin/env bash
set -euo pipefail

collect_row() {
  local name="$1"
  local sku="$2"
  local opening="$3"
  local granted="$4"
  local attempts="$5"
  local final="$6"
  local oversell="false"
  if (( granted > opening )); then
    oversell="true"
  fi
  if (( final < 0 )); then
    oversell="true"
  fi
  python3 - <<PY
import json
print(json.dumps({
  "name": "$name",
  "sku": "$sku",
  "oversell_detected": $oversell,
  "total_granted": int($granted),
  "final_stock": int($final),
  "requests_attempted": int($attempts),
}))
PY
}
