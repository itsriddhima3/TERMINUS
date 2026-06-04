#!/usr/bin/env bash
set -euo pipefail

/app/init/ensure_pg.sh
mkdir -p /app/output

python3 - <<'PY'
import json
import subprocess
from pathlib import Path

matrix = json.loads(Path("/app/data/workload_matrix.json").read_text(encoding="utf-8"))
region_id = matrix["filter_region_id"]
zone_code = matrix["filter_zone_code"]

proc = subprocess.run(
    ["bash", "/app/lib/explain_collect.sh", str(region_id), zone_code],
    check=True,
    text=True,
    capture_output=True,
)
plan = json.loads(proc.stdout.strip())

join_counts = {"Nested Loop": 0, "Hash Join": 0, "Merge Join": 0}
bridge_est = None
spine_driver = "other"

def collect_aliases(node):
    rel = node.get("Relation Name") or node.get("Alias") or ""
    found = {rel} if rel else set()
    for sub in node.get("Plans") or []:
        found |= collect_aliases(sub)
    return found

def walk(node):
    global bridge_est, spine_driver
    ntype = node.get("Node Type", "")
    if ntype in join_counts:
        join_counts[ntype] += 1
        children = node.get("Plans") or []
        if len(children) >= 2 and spine_driver != "hash_join":
            aliases = collect_aliases(children[0]) | collect_aliases(children[1])
            if {"fs", "fact_shipment"} & aliases and {"bf", "bridge_facility_zone"} & aliases:
                candidate = ntype.replace(" ", "_").lower()
                if spine_driver == "other" or candidate == "hash_join":
                    spine_driver = candidate
    rel = node.get("Relation Name") or node.get("Alias") or ""
    if rel in ("bf", "bridge_facility_zone"):
        bridge_est = node.get("Plan Rows")
    for sub in node.get("Plans") or []:
        walk(sub)

walk(plan[0]["Plan"])

plan_rows = plan[0]["Plan"].get("Plan Rows")

count_sql = (
    f"sed -e 's/__REGION__/{region_id}/g' -e 's/__ZONE__/{zone_code}/g' "
    "/app/q/spine_template.sql | psql_as_planner -t -A -f -"
)
count_proc = subprocess.run(
    ["bash", "-lc", f"source /app/lib/psql_wrap.sh && {count_sql}"],
    check=True,
    text=True,
    capture_output=True,
    timeout=120,
)
result_total = int(count_proc.stdout.strip())

bridge_count_sql = (
    f"SELECT count(*) FROM bridge_facility_zone "
    f"WHERE region_id = {region_id} AND zone_code = '{zone_code}'"
)
bridge_proc = subprocess.run(
    ["bash", "-lc", f"source /app/lib/psql_wrap.sh && psql_as_planner -t -A -c \"{bridge_count_sql}\""],
    check=True,
    text=True,
    capture_output=True,
)
bridge_actual = int(bridge_proc.stdout.strip())
bridge_ratio = bridge_actual / max(bridge_est or 1, 1)

inventory_count_sql = (
    f"SELECT count(*) FROM fact_inventory_snapshot "
    f"WHERE region_id = {region_id} AND zone_code = '{zone_code}'"
)
inventory_proc = subprocess.run(
    ["bash", "-lc", f"source /app/lib/psql_wrap.sh && psql_as_planner -t -A -c \"{inventory_count_sql}\""],
    check=True,
    text=True,
    capture_output=True,
)
inventory_actual = int(inventory_proc.stdout.strip())

inventory_explain_sql = (
    f"EXPLAIN (FORMAT JSON) SELECT 1 FROM fact_inventory_snapshot "
    f"WHERE region_id = {region_id} AND zone_code = '{zone_code}'"
)
inventory_explain_proc = subprocess.run(
    ["bash", "-lc", f"source /app/lib/psql_wrap.sh && psql_as_planner -t -A -c \"{inventory_explain_sql}\""],
    check=True,
    text=True,
    capture_output=True,
)
inventory_plan = json.loads(inventory_explain_proc.stdout.strip())[0]["Plan"]
inventory_est = inventory_plan.get("Plan Rows")
inventory_ratio = inventory_actual / max(inventory_est or 1, 1)

report = {
    "schema_version": matrix["schema_version"],
    "workload_label": matrix["workload_label"],
    "catalog_tables": matrix["catalog_tables"],
    "filter_region_id": region_id,
    "filter_zone_code": zone_code,
    "result_total": result_total,
    "join_methods": {
        "nested_loop_count": join_counts["Nested Loop"],
        "hash_join_count": join_counts["Hash Join"],
        "merge_join_count": join_counts["Merge Join"],
    },
    "spine_driver": spine_driver,
    "bridge_estimate_ratio": round(bridge_ratio, 4),
    "inventory_estimate_ratio": round(inventory_ratio, 4),
    "plan_root_rows": plan_rows,
    "actual_root_rows": result_total,
}

Path("/app/output/plan_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
PY
