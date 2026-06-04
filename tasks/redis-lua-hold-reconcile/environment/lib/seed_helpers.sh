#!/usr/bin/env bash
set -euo pipefail

source /app/lib/redis_wrap.sh

seed_catalog() {
  python3 - <<'PY'
import json
from pathlib import Path
import subprocess

catalog = json.loads(Path("/app/data/sku_catalog.json").read_text())
alias = {
    "Alpha-Unit": "hold:alpha",
    "Beta-Crate": "hold:beta",
    "Gamma-Tote": "hold:gamma",
}
for row in catalog:
    key = row["key"]
    opening = row["opening_units"]
    hold = alias[row["label"]]
    subprocess.run(["redis-cli", "SET", key, str(opening)], check=True)
    subprocess.run(["redis-cli", "SET", hold, str(opening)], check=True)
PY
}

reset_scenario() {
  local sku_label="$1"
  local opening="$2"
  python3 - <<PY
import json, subprocess
from pathlib import Path
label = """$sku_label"""
opening = int("""$opening""")
catalog = json.loads(Path("/app/data/sku_catalog.json").read_text())
alias = {"Alpha-Unit": "hold:alpha", "Beta-Crate": "hold:beta", "Gamma-Tote": "hold:gamma"}
for row in catalog:
    if row["label"] == label:
        subprocess.run(["redis-cli", "SET", row["key"], str(opening)], check=True)
        subprocess.run(["redis-cli", "SET", alias[label], str(opening)], check=True)
        break
PY
}

canonical_key() {
  local label="$1"
  python3 - <<PY
import json
from pathlib import Path
label = """$label"""
for row in json.loads(Path("/app/data/sku_catalog.json").read_text()):
    if row["label"] == label:
        print(row["key"])
        break
PY
}

worker_slot() {
  source /app/lib/k7m/step_w1.sh
  step_w1 "$1"
}
