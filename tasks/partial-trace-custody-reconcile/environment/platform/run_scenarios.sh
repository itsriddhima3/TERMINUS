#!/bin/bash
set -uo pipefail

mkdir -p /app/output

sweep_rc=0

mapfile -t SCENARIO_IDS < <(
  python3 -c 'import json; print("\n".join(json.load(open("/app/config/scenarios.json"))["scenario_ids"]))'
)

for sid in "${SCENARIO_IDS[@]}"; do
  /app/bin/route_pack "/app/cases/${sid}" "/app/output/.pack_${sid}.json"
  rc=$?
  if [[ $rc -ne 0 ]]; then
    sweep_rc=$rc
  fi
done

python3 /app/scripts/bundle_merge.py
exit "$sweep_rc"
