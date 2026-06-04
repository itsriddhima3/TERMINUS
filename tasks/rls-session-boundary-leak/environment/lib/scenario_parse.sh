#!/usr/bin/env bash
set -euo pipefail

parse_switch_block() {
  local raw="$1"
  local prefix="$2"
  python3 - <<'PY' "$raw" "$prefix"
import json, sys
raw, prefix = sys.argv[1], sys.argv[2]
noise = {
    "SET", "PREPARE", "EXECUTE", "DEALLOCATE", "BEGIN", "COMMIT", "ROLLBACK",
    "SAVEPOINT", "RELEASE",
}
if "---SWITCH---" in raw:
    block = raw.split("---SWITCH---", 1)[1]
else:
    block = raw
labels = [
    line.strip()
    for line in block.splitlines()
    if line.strip() and line.strip() not in noise and not line.strip().startswith("---")
]
foreign = [label for label in labels if not label.startswith(prefix)]
print(json.dumps({
    "cross_scope_visible": bool(foreign),
    "foreign_labels_seen": foreign,
    "owned_row_count": len(labels),
}))
PY
}

parse_switch_count() {
  local raw="$1"
  local expected="$2"
  python3 - <<'PY' "$raw" "$expected"
import json, re, sys
raw, expected = sys.argv[1], int(sys.argv[2])
if "---SWITCH---" in raw:
    block = raw.split("---SWITCH---", 1)[1]
else:
    block = raw
numbers = [int(match) for match in re.findall(r"^\d+$", block, re.MULTILINE)]
value = numbers[-1] if numbers else int(block.strip().splitlines()[0].strip())
print(json.dumps({
    "cross_scope_visible": value != expected,
    "foreign_labels_seen": [] if value == expected else [f"count:{value}"],
    "owned_row_count": value,
}))
PY
}

parse_switch_tokens() {
  local raw="$1"
  local allowed_prefix="$2"
  python3 - <<'PY' "$raw" "$allowed_prefix"
import json, sys
raw, allowed = sys.argv[1], sys.argv[2]
noise = {
    "SET", "PREPARE", "EXECUTE", "DEALLOCATE", "BEGIN", "COMMIT", "ROLLBACK",
    "SAVEPOINT", "RELEASE",
}
if "---SWITCH---" in raw:
    block = raw.split("---SWITCH---", 1)[1]
else:
    block = raw
tokens = [
    line.strip()
    for line in block.splitlines()
    if line.strip() and line.strip() not in noise and not line.strip().startswith("---")
]
foreign = [tok for tok in tokens if not tok.startswith(allowed)]
print(json.dumps({
    "cross_scope_visible": bool(foreign),
    "foreign_labels_seen": foreign,
    "owned_row_count": len(tokens),
}))
PY
}
