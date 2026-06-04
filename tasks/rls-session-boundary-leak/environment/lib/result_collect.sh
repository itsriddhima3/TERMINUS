#!/usr/bin/env bash
set -euo pipefail

collect_labels() {
  local raw="$1"
  python3 - <<'PY' "$raw"
import json, sys
raw = sys.argv[1]
labels = []
for line in raw.splitlines():
    line = line.strip()
    if not line or line.startswith("(") or line.startswith("-") or line.startswith("label"):
        continue
    labels.append(line)
print(json.dumps(labels))
PY
}
