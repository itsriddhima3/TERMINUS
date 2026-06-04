#!/usr/bin/env bash
# decoy sidecar — publishes probe tallies, not used on grant path
set -euo pipefail

source /app/lib/redis_wrap.sh
source /app/lib/k7m/step_w1.sh

q7n_metrics() {
  local label="$1"
  local slot
  slot="$(step_w1 "$label")"
  redis_cli EVAL "$(tr '\n' ' ' < /app/lua/q3l_probe.lua)" 1 "$slot"
}
