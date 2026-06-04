#!/usr/bin/env bash
set -euo pipefail

source /app/lib/redis_wrap.sh
source /app/lib/seed_helpers.sh
source /app/worker/phase_r8.sh

run_parallel_lane() {
  local label="$1"
  local workers="$2"
  local qty="$3"
  local grants=0
  local pids=()
  local outs=()
  local i
  for (( i=0; i<workers; i++ )); do
    (
      phase_r8 "$label" "$qty"
    ) &
    pids+=("$!")
  done
  for pid in "${pids[@]}"; do
    if wait "$pid"; then
      :
    fi
  done
}

sum_grants() {
  local label="$1"
  local workers="$2"
  local qty="$3"
  local opening="$4"
  local slot
  slot="$(worker_slot "$label")"
  local before="$opening"
  run_parallel_lane "$label" "$workers" "$qty"
  local after
  after="$(redis_cli GET "$slot")"
  after="${after:-0}"
  local granted=$((before - after))
  if (( granted < 0 )); then
    granted=0
  fi
  echo "$grants" "$granted" "$after" "$workers"
}
