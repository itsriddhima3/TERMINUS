#!/bin/bash
set -uo pipefail

REGISTRY="/app/config/case_registry.json"
BUNDLE="/app/output/verdict_bundle.json"
MARKED_DIR="/app/output/marked"

mkdir -p "$MARKED_DIR" /app/output

sweep_rc=0

mapfile -t PACK_IDS < <(
  python3 -c 'import json; print("\n".join(json.load(open("/app/config/case_registry.json"))["pack_ids"]))'
)

for pack_id in "${PACK_IDS[@]}"; do
  runner="/app/flow-src/run_${pack_id}.lua"
  if [[ ! -f "$runner" ]]; then
    runner="/app/flow-src/run_pack.lua"
  fi
  lua5.4 "$runner" "$pack_id"
  pack_rc=$?
  sweep_rc=$pack_rc
done

python3 /app/scripts/bundle_merge.py

exit "$sweep_rc"
