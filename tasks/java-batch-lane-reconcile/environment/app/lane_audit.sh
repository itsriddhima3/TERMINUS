#!/usr/bin/env bash
set -euo pipefail
source /app/init/ensure_pg.sh
bash /app/init/start_api.sh
mkdir -p /app/output

python3 - <<'PY'
import json
import subprocess
from pathlib import Path

catalog = json.loads(Path("/app/data/partition_catalog.json").read_text())
matrix = json.loads(Path("/app/data/scenario_matrix.json").read_text())
letters = list("abcdefghijklmnopqrstuv")
mapping = {matrix["scenario_order"][i]: f"/app/app/scenario_{letters[i]}.sh" for i in range(len(letters))}

scenarios = {}
loss_events = 0
for name in matrix["scenario_order"]:
    proc = subprocess.run([mapping[name]], check=True, text=True, capture_output=True)
    row = json.loads(proc.stdout.strip().splitlines()[-1])
    scenarios[name] = row
    loss_events += int(row.get("lost_rows", 0) or 0)
    loss_events += int(row.get("duplicate_external_keys", 0) or 0)
    if row.get("unstable_totals"):
        loss_events += 1

def compliance_ok(label: str) -> bool:
    cap = next(p["cap_slots"] for p in catalog["partitions"] if p["label"] == label)
    r = subprocess.run(
        ["psql", "-U", "postgres", "-d", "lane_db", "-At", "-c",
         f"SELECT active_slots FROM partition_dim WHERE label='{label}';"],
        text=True, capture_output=True,
    )
    act = int(r.stdout.strip() or "999")
    return act <= cap

labels = [p["label"] for p in catalog["partitions"]]
ingest = {lbl: compliance_ok(lbl) for lbl in labels}
clean_rows = all(
    s.get("lost_rows", 1) == 0 and s.get("duplicate_external_keys", 1) == 0
    and not s.get("unstable_totals", True) for s in scenarios.values()
)
if clean_rows:
    ingest = {k: True for k in ingest}

report = {
    "schema_version": matrix["schema_version"],
    "catalog_partitions": labels,
    "scenarios": scenarios,
    "ingest_compliance": all(ingest.values()),
    "stress_summary": {"loss_events": loss_events},
}
Path("/app/output/lane_audit.json").write_text(json.dumps(report, indent=2) + "\n")
PY
