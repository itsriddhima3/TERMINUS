#!/usr/bin/env bash
set -euo pipefail

source /app/lib/redis_wrap.sh
source /app/lib/k7m/step_w1.sh
source /app/lib/k7m/q7n_frame.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLICY="/app/config/worker_policy.toml"

read_forward_policy() {
  python3 - <<'PY'
from pathlib import Path
text = Path("/app/config/worker_policy.toml").read_text()
flag = False
for line in text.splitlines():
    line = line.strip()
    if line.startswith("forward_observation_frame"):
        _, _, val = line.partition("=")
        flag = val.strip().lower() in {"1", "true", "yes"}
        break
print("1" if flag else "0")
PY
}

phase_r8() {
  local label="$1"
  local qty="$2"
  local slot
  slot="$(step_w1 "$label")"
  local obs
  obs="$(q7n_frame "$slot")"
  obs="${obs:-0}"
  if (( obs < qty )); then
    echo 0
    return 0
  fi
  local lua_body
  lua_body="$(tr '\n' ' ' < "${SCRIPT_DIR}/../lua/op_n2.lua")"
  local out
  if [[ "$(read_forward_policy)" == "1" ]]; then
    out="$(redis_cli EVAL "$lua_body" 1 "$slot" "$qty" "$obs")"
  else
    out="$(redis_cli EVAL "$lua_body" 1 "$slot" "$qty")"
  fi
  echo "${out:-0}"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  phase_r8 "$@"
fi
