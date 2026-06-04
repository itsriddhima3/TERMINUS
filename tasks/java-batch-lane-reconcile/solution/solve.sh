#!/bin/bash
set -euo pipefail

bash /app/init/ensure_pg.sh
bash /app/init/start_api.sh

if [[ -f lane-fix.patch ]]; then
  cp lane-fix.patch /app/lane-fix.patch
else
  cp /solution/lane-fix.patch /app/lane-fix.patch
fi
cd /app
patch -p1 --forward < lane-fix.patch

psql -U postgres -d lane_db -v ON_ERROR_STOP=1 -f /app/db/functions/step_w1.sql
psql -U postgres -d lane_db -v ON_ERROR_STOP=1 <<'SQL'
DROP TRIGGER IF EXISTS trg_step_w1 ON line_slice;
CREATE TRIGGER trg_step_w1
  AFTER INSERT OR UPDATE OR DELETE ON line_slice
  FOR EACH ROW EXECUTE FUNCTION step_w1();
SQL

cd /app/api
mvn -o -q -DskipTests package
cp target/lane-api.jar /app/api/lane-api.jar

if [[ -f /var/run/lane-api.pid ]]; then
  kill "$(cat /var/run/lane-api.pid)" 2>/dev/null || true
  rm -f /var/run/lane-api.pid
fi
bash /app/init/start_api.sh

mkdir -p /app/output
bash /app/app/lane_audit.sh

python3 <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/app/output/lane_audit.json").read_text(encoding="utf-8"))
for key, row in report["scenarios"].items():
    if row.get("lost_rows") or row.get("duplicate_external_keys") or row.get("unstable_totals"):
        raise SystemExit(f"scenario {key} still dirty: {row}")
if report["stress_summary"]["loss_events"] != 0:
    raise SystemExit("stress_summary not clean")
if not report["ingest_compliance"]:
    raise SystemExit("ingest_compliance false")
PY
