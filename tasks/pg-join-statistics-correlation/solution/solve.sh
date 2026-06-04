#!/bin/bash
set -euo pipefail

/app/init/ensure_pg.sh

cat > /app/store/a7k.sql <<'SQL'
ALTER TABLE bridge_facility_zone ALTER COLUMN region_id SET STATISTICS 1000;
ALTER TABLE bridge_facility_zone ALTER COLUMN zone_code SET STATISTICS 1000;
ALTER TABLE fact_shipment ALTER COLUMN region_id SET STATISTICS 1000;
ALTER TABLE fact_shipment ALTER COLUMN zone_code SET STATISTICS 1000;
ALTER TABLE fact_inventory_snapshot ALTER COLUMN region_id SET STATISTICS 1000;
ALTER TABLE fact_inventory_snapshot ALTER COLUMN zone_code SET STATISTICS 1000;
ALTER TABLE dim_zone ALTER COLUMN region_id SET STATISTICS 500;
ALTER TABLE dim_zone ALTER COLUMN zone_code SET STATISTICS 500;
ALTER TABLE dim_facility ALTER COLUMN region_id SET STATISTICS 500;
SQL

cat > /app/migrations/x9k.sql <<'SQL'
DROP STATISTICS IF EXISTS st_x9;
CREATE STATISTICS st_x9 (dependencies) ON region_id, zone_code FROM bridge_facility_zone;

DROP STATISTICS IF EXISTS st_x9b;
CREATE STATISTICS st_x9b (dependencies) ON region_id, zone_code FROM fact_shipment;

DROP STATISTICS IF EXISTS st_x9c;
CREATE STATISTICS st_x9c (dependencies) ON region_id, zone_code FROM fact_inventory_snapshot;

DROP STATISTICS IF EXISTS st_x9d;
CREATE STATISTICS st_x9d (dependencies) ON region_id, zone_code FROM dim_zone;
SQL

cat > /app/lib/r2k.sql <<'SQL'
ANALYZE dim_region;
ANALYZE dim_facility;
ANALYZE dim_zone;
ANALYZE dim_lane;
ANALYZE dim_carrier;
ANALYZE dim_sku;
ANALYZE dim_supplier;
ANALYZE bridge_facility_zone;
ANALYZE bridge_lane_carrier;
ANALYZE fact_shipment;
ANALYZE fact_shipment_line;
ANALYZE fact_route_leg;
ANALYZE fact_inventory_snapshot;
ANALYZE fact_handling_event;
ANALYZE fact_charge;
SQL

for sql_file in /app/store/a7k.sql /app/migrations/x9k.sql /app/lib/r2k.sql; do
  psql -U postgres -d logistics_db -v ON_ERROR_STOP=1 -f "$sql_file"
done

psql -U postgres -d logistics_db -v ON_ERROR_STOP=1 <<'SQL'
ANALYZE bridge_facility_zone;
ANALYZE fact_shipment;
ANALYZE fact_inventory_snapshot;
ANALYZE dim_zone;
SQL

python3 - <<'PY'
import json
import subprocess
import time
from pathlib import Path

matrix = json.loads(Path("/app/data/workload_matrix.json").read_text(encoding="utf-8"))
bands = matrix["acceptance_bands"]

report = None
last_error = None
for attempt in range(5):
    try:
        subprocess.run(["bash", "/app/app/plan_audit.sh"], check=True)
        report = json.loads(Path("/app/output/plan_audit.json").read_text(encoding="utf-8"))
        break
    except subprocess.CalledProcessError as exc:
        last_error = exc
        time.sleep(1)
if report is None:
    raise SystemExit(f"plan_audit failed after retries: {last_error}")

for field, lo_key, hi_key in (
    ("bridge_estimate_ratio", "bridge_estimate_ratio_min", "bridge_estimate_ratio_max"),
    ("inventory_estimate_ratio", "inventory_estimate_ratio_min", "inventory_estimate_ratio_max"),
):
    ratio = report[field]
    if not (bands[lo_key] <= ratio <= bands[hi_key]):
        raise SystemExit(f"{field} {ratio} outside band")

if report["join_methods"]["hash_join_count"] < bands["hash_join_count_min"]:
    raise SystemExit("insufficient hash joins")

methods = report["join_methods"]
total_joins = (
    methods["hash_join_count"] + methods["nested_loop_count"] + methods["merge_join_count"]
)
if total_joins > 0:
    share = methods["hash_join_count"] / total_joins
    if share < bands["hash_join_share_min"]:
        raise SystemExit("insufficient hash join share")

if report["join_methods"]["nested_loop_count"] > bands["nested_loop_count_max"]:
    raise SystemExit("too many nested loops")

if report["spine_driver"] == bands["forbidden_spine_driver"]:
    raise SystemExit("forbidden spine driver")

total = report["result_total"]
if not (bands["result_total_min"] <= total <= bands["result_total_max"]):
    raise SystemExit(f"result total {total} outside band")
PY
