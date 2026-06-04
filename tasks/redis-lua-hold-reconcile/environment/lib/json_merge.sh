#!/usr/bin/env bash
set -euo pipefail

# merge partial JSON objects (helper for audit assembly)
json_merge() {
  local a="$1"
  local b="$2"
  python3 - <<PY
import json, sys
left = json.loads(open("$a").read())
right = json.loads(open("$b").read())
if isinstance(left, dict) and isinstance(right, dict):
    left.update(right)
print(json.dumps(left))
PY
}
