# noqa: D100
"""Blob definitions for gen_java_batch_lane.py"""

DOCKERFILE = r'''FROM debian:bookworm-slim@sha256:67b30a61dc87758f0caf819646104f29ecbda97d920aaf5edc834128ac8493d3 AS build-api

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates=20230311+deb12u1 \
        maven=3.8.7-1 \
        openjdk-17-jdk-headless=17.0.19+10-1~deb12u2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY api/pom.xml api/pom.xml
RUN mvn -f api/pom.xml -q dependency:go-offline
COPY api/src api/src
RUN mvn -f api/pom.xml -q -DskipTests package

FROM postgres:15-bookworm@sha256:9010f897603ef2bd8aa668ecde230fc9eb4d564961569fee243bc919b1f07b3e

LABEL org.opencontainers.image.title="java-batch-lane-reconcile"
LABEL org.opencontainers.image.source="https://github.com/laude-institute/terminal-bench"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"

ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=lane_db
ENV PATH="/root/.local/bin:${PATH}" \
    UV_CACHE_DIR="/opt/uv-cache" \
    UV_OFFLINE=1 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

ARG UV_VERSION=0.9.5
ARG UV_SHA256=2cf10babba653310606f8b49876cfb679928669e7ddaa1fb41fb00ce73e64f66

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        ca-certificates=20230311+deb12u1 \
        curl=7.88.1-10+deb12u14 \
        jq=1.6-2.1+deb12u1 \
        openjdk-17-jre-headless=17.0.19+10-1~deb12u2 \
        maven=3.8.7-1 \
        openjdk-17-jdk-headless=17.0.19+10-1~deb12u2 \
        python3=3.11.2-1+b1 \
        tmux=3.3a-3 \
    && mkdir -p /root/.local/bin \
    && curl -fsSL --retry 5 --retry-all-errors --retry-delay 2 \
        "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" \
        -o /tmp/uv.tar.gz \
    && echo "${UV_SHA256}  /tmp/uv.tar.gz" | sha256sum -c - \
    && mkdir -p /tmp/uv-unpack \
    && tar -xzf /tmp/uv.tar.gz -C /tmp/uv-unpack \
    && install -m 0755 /tmp/uv-unpack/uv-x86_64-unknown-linux-gnu/uv /root/.local/bin/uv \
    && install -m 0755 /tmp/uv-unpack/uv-x86_64-unknown-linux-gnu/uvx /root/.local/bin/uvx \
    && rm -rf /tmp/uv.tar.gz /tmp/uv-unpack \
    && printf '%s\n' \
        'export PATH="/root/.local/bin:${PATH}"' \
        'export UV_CACHE_DIR="/opt/uv-cache"' \
        > /root/.local/bin/env \
    && . /root/.local/bin/env \
    && mkdir -p "${UV_CACHE_DIR}" \
    && chmod 777 "${UV_CACHE_DIR}" \
    && UV_OFFLINE=0 uvx -p 3.13 \
        -w pytest==8.4.1 \
        -w pytest-json-ctrf==0.3.5 \
        pytest --version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=build-api /build/api/target/lane-api.jar /app/api/lane-api.jar
COPY api/pom.xml /app/api/pom.xml
COPY api/src /app/api/src
COPY db/migration /app/db/migration
COPY db/functions /app/db/functions
COPY api/src/main/resources/application.yml /app/api/application.yml
COPY api/src/main/resources/application-prod.yml /app/api/application-prod.yml
COPY --chmod=0755 init /app/init
COPY --chmod=0755 app /app/app
COPY --chmod=0755 lib /app/lib
COPY data /app/data
COPY config /app/config
COPY docs /app/docs
COPY decoy /app/decoy

COPY --chmod=0755 init/docker-entrypoint-wrapper.sh /usr/local/bin/docker-entrypoint-wrapper.sh

ENTRYPOINT ["docker-entrypoint-wrapper.sh"]
CMD ["sleep", "infinity"]
'''

INIT = {
    "docker-entrypoint-wrapper.sh": """#!/usr/bin/env bash
set -euo pipefail
/usr/local/bin/docker-entrypoint.sh postgres &
until pg_isready -U "${POSTGRES_USER:-postgres}" -q; do sleep 0.2; done
exec "$@"
""",
    "ensure_pg.sh": """#!/usr/bin/env bash
set -euo pipefail
wait_for_pg() {
  local tries=150
  while (( tries > 0 )); do
    if pg_isready -U "${POSTGRES_USER:-postgres}" -q 2>/dev/null; then
      if psql -U "${POSTGRES_USER:-postgres}" -d postgres -At -c "SELECT 1" >/dev/null 2>&1; then
        return 0
      fi
    fi
    sleep 0.2
    tries=$((tries - 1))
  done
  return 1
}
wait_for_pg
bash /app/init/bootstrap_once.sh
""",
    "bootstrap_once.sh": """#!/usr/bin/env bash
set -euo pipefail
FLAG=/var/lib/postgresql/lane_bootstrapped
if [[ -f "$FLAG" ]]; then
  exit 0
fi
bash /app/init/bootstrap.sh
touch "$FLAG"
""",
    "bootstrap.sh": """#!/usr/bin/env bash
set -euo pipefail
export PGUSER="${POSTGRES_USER:-postgres}"
export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
mkdir -p /app/output
chmod 777 /app/output
bash /app/init/post_boot.sh
""",
    "post_boot.sh": """#!/usr/bin/env bash
set -euo pipefail
mkdir -p /app/output
chmod 777 /app/output
""",
    "start_api.sh": """#!/usr/bin/env bash
set -euo pipefail
source /app/init/ensure_pg.sh
export SPRING_CONFIG_LOCATION="file:/app/api/application.yml,file:/app/api/application-prod.yml"
export SPRING_FLYWAY_LOCATIONS="filesystem:/app/db/migration"
if [[ -f /var/run/lane-api.pid ]]; then
  if kill -0 "$(cat /var/run/lane-api.pid)" 2>/dev/null; then
    exit 0
  fi
fi
nohup java -jar /app/api/lane-api.jar > /app/output/api.log 2>&1 &
echo $! > /var/run/lane-api.pid
for i in $(seq 1 120); do
  if curl -fsS http://127.0.0.1:8080/actuator/health >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.5
done
echo "API failed to become healthy" >&2
exit 1
""",
}

DB = {
    "migration/V1__extensions.sql": "CREATE EXTENSION IF NOT EXISTS pgcrypto;\n",
    "migration/V2__core_tables.sql": """\
CREATE TABLE partition_dim (
  label TEXT PRIMARY KEY,
  cap_slots INT NOT NULL,
  active_slots INT NOT NULL DEFAULT 0,
  rollup_qty BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE header_slice (
  id BIGSERIAL PRIMARY KEY,
  partition_label TEXT NOT NULL REFERENCES partition_dim(label),
  external_biz_id TEXT NOT NULL,
  stamp_version BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (partition_label, external_biz_id)
);

CREATE TABLE line_slice (
  id BIGSERIAL PRIMARY KEY,
  header_id BIGINT NOT NULL REFERENCES header_slice(id) ON DELETE CASCADE,
  sku TEXT NOT NULL,
  qty INT NOT NULL CHECK (qty > 0),
  stamp_version BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX idx_line_header ON line_slice(header_id);

CREATE TABLE lane_attempt (
  id BIGSERIAL PRIMARY KEY,
  partition_label TEXT NOT NULL,
  external_biz_id TEXT NOT NULL,
  accepted_lines INT NOT NULL DEFAULT 0,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO partition_dim(label, cap_slots) VALUES
  ('North-Shelf', 6),
  ('East-Crate', 10),
  ('West-Bin', 4);
""",
    "migration/V3__rollup.sql": """\
\\i /app/db/functions/step_w1.sql

DROP TRIGGER IF EXISTS trg_step_w1 ON line_slice;
CREATE TRIGGER trg_step_w1
  AFTER INSERT OR UPDATE OR DELETE ON line_slice
  FOR EACH ROW EXECUTE FUNCTION step_w1();
""",
    "functions/step_w1.sql": """\
CREATE OR REPLACE FUNCTION step_w1()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  hdr TEXT;
  delta BIGINT := 0;
BEGIN
  IF TG_OP = 'DELETE' THEN
    SELECT h.partition_label INTO hdr FROM header_slice h WHERE h.id = OLD.header_id;
    delta := -OLD.qty;
    PERFORM 1 FROM line_slice WHERE header_id = OLD.header_id FOR UPDATE;
    PERFORM 1 FROM header_slice WHERE id = OLD.header_id FOR UPDATE;
  ELSIF TG_OP = 'UPDATE' THEN
    SELECT h.partition_label INTO hdr FROM header_slice h WHERE h.id = NEW.header_id;
    delta := NEW.qty - OLD.qty;
    PERFORM 1 FROM line_slice WHERE id = NEW.id FOR UPDATE;
    PERFORM 1 FROM header_slice WHERE id = NEW.header_id FOR UPDATE;
  ELSE
    SELECT h.partition_label INTO hdr FROM header_slice h WHERE h.id = NEW.header_id;
    delta := NEW.qty;
    PERFORM 1 FROM line_slice WHERE id = NEW.id FOR UPDATE;
    PERFORM 1 FROM header_slice WHERE id = NEW.header_id FOR UPDATE;
  END IF;
  UPDATE partition_dim SET rollup_qty = rollup_qty + delta WHERE label = hdr;
  RETURN COALESCE(NEW, OLD);
END;
$$;
""",
    "functions/audit_scalar.sql": """\
CREATE OR REPLACE FUNCTION audit_scalar(p_label TEXT)
RETURNS BIGINT
LANGUAGE sql
STABLE
AS $$
  SELECT COALESCE((SELECT rollup_qty FROM partition_dim WHERE label = p_label), 0);
$$;
""",
}

# Flyway cannot use \i - fix V3 to inline or use separate approach
DB["migration/V3__rollup.sql"] = (
    DB["functions/step_w1.sql"]
    + """
DROP TRIGGER IF EXISTS trg_step_w1 ON line_slice;
CREATE TRIGGER trg_step_w1
  AFTER INSERT OR UPDATE OR DELETE ON line_slice
  FOR EACH ROW EXECUTE FUNCTION step_w1();
"""
)

RUN_SCENARIO_SH = r'''#!/usr/bin/env bash
set -euo pipefail
KEY="$1"
source /app/lib/curl_wrap.sh
source /app/lib/psql_wrap.sh
bash /app/init/start_api.sh

reset_lane() {
  api_reset
  psql_lane -c "TRUNCATE line_slice, header_slice RESTART IDENTITY CASCADE;"
  psql_lane -c "UPDATE partition_dim SET active_slots=0, rollup_qty=0;"
}

new_biz() {
  python3 -c 'import uuid; print(uuid.uuid4().hex[:16])'
}

post_chunk() {
  local label="$1"
  local biz="$2"
  local sku="$3"
  local qty="$4"
  api_post_batch "$label" "{\"externalBizId\":\"$biz\",\"lines\":[{\"sku\":\"$sku\",\"qty\":$qty}]}"
}

count_lines() {
  local label="$1"
  psql_lane -At -c "SELECT COUNT(*) FROM line_slice l JOIN header_slice h ON h.id=l.header_id WHERE h.partition_label='$label';"
}

count_dup_biz() {
  psql_lane -At -c "SELECT COALESCE(SUM(GREATEST(cnt-1,0)),0) FROM (SELECT h.external_biz_id, COUNT(l.id) cnt FROM header_slice h JOIN line_slice l ON l.header_id=h.id GROUP BY h.partition_label, h.external_biz_id) s;"
}

rollup_of() {
  local label="$1"
  psql_lane -At -c "SELECT rollup_qty FROM partition_dim WHERE label='$label';"
}

active_of() {
  local label="$1"
  psql_lane -At -c "SELECT active_slots FROM partition_dim WHERE label='$label';"
}

run_case() {
  local key="$KEY"
  reset_lane
  local lost=0 dup=0 unstable=0 chunks=0 parity=1 monotone=1 raw=1
  local label_n="North-Shelf" label_e="East-Crate" label_w="West-Bin"
  case "$key" in
    w1_single)
      chunks=3
      for i in 1 2 3; do
        r=$(post_chunk "$label_n" "$(new_biz)" "NS-$i" 1)
        acc=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('accepted',0))" "$r")
        lost=$((lost + 1 - acc))
      done
      ;;
    w2_pair)
      chunks=6
      for w in 1 2; do
        (
          for i in 1 2 3; do
            post_chunk "$label_n" "$(new_biz)" "P${w}-$i" 1 >/dev/null
          done
        ) &
      done
      wait
      ;;
    w4_quad)
      chunks=12
      for w in 1 2 3 4; do
        ( for i in 1 2 3; do post_chunk "$label_e" "$(new_biz)" "Q${w}-$i" 1 >/dev/null; done ) &
      done
      wait
      ;;
    mix_parallel)
      chunks=8
      ( for i in 1 2 3 4; do post_chunk "$label_n" "$(new_biz)" "MN-$i" 1 >/dev/null; done ) &
      ( for i in 1 2 3 4; do post_chunk "$label_w" "$(new_biz)" "MW-$i" 1 >/dev/null; done ) &
      wait
      ;;
    deplete_exact)
      chunks=6
      for i in $(seq 1 6); do post_chunk "$label_n" "$(new_biz)" "DE-$i" 1 >/dev/null; done
      ;;
    pipe_backlog)
      chunks=10
      for i in $(seq 1 10); do post_chunk "$label_e" "$(new_biz)" "PB-$i" 1 >/dev/null; done
      ;;
    idempotent_rerun)
      chunks=4
      b=$(new_biz)
      for i in 1 2; do post_chunk "$label_n" "$b" "RR-1" 1 >/dev/null; done
      ;;
    over_cap_reject)
      chunks=8
      for i in $(seq 1 8); do post_chunk "$label_w" "$(new_biz)" "OC-$i" 1 >/dev/null; done
      ;;
    interleave_ab)
      chunks=6
      for i in 1 2 3; do
        post_chunk "$label_n" "$(new_biz)" "IA-N$i" 2 >/dev/null
        post_chunk "$label_e" "$(new_biz)" "IA-E$i" 2 >/dev/null
      done
      ;;
    partial_abort)
      chunks=1
      curl -s -o /tmp/pa.json -w "%{http_code}" -X POST "http://127.0.0.1:8080/api/partition/${label_n}/batch" \
        -H 'Content-Type: application/json' -d '{"externalBizId":"abort-case","lines":[{"sku":"AB","qty":1},{"sku":"ZZ","qty":-9}]}' >/dev/null || true
      ;;
    stamp_guard)
      chunks=2
      b=$(new_biz)
      post_chunk "$label_n" "$b" "SG-1" 1 >/dev/null
      post_chunk "$label_n" "$b" "SG-2" 2 >/dev/null
      ;;
    post_write_snap)
      chunks=1
      b=$(new_biz)
      post_chunk "$label_e" "$b" "SN-1" 1 >/dev/null
      snap=$(api_snapshot "$label_e")
      raw=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(1 if d.get('lineCount',0)>=1 else 0)" "$snap")
      ;;
    sibling_contention)
      chunks=9
      ( for i in 1 2 3; do post_chunk "$label_n" "$(new_biz)" "SC-N$i" 1 >/dev/null; done ) &
      ( for i in 1 2 3 4 5 6; do post_chunk "$label_e" "$(new_biz)" "SC-E$i" 1 >/dev/null; done ) &
      wait
      ;;
    pool_dual_conn)
      chunks=2
      post_chunk "$label_n" "$(new_biz)" "PD-1" 1 >/dev/null
      post_chunk "$label_n" "$(new_biz)" "PD-2" 1 >/dev/null
      ;;
    parity_probe)
      chunks=2
      post_chunk "$label_w" "$(new_biz)" "PP-1" 1 >/dev/null
      post_chunk "$label_w" "$(new_biz)" "PP-2" 1 >/dev/null
      ;;
    biz_key_race)
      chunks=2
      b=$(new_biz)
      ( post_chunk "$label_e" "$b" "RK-1" 1 >/dev/null ) &
      ( post_chunk "$label_e" "$b" "RK-2" 1 >/dev/null ) &
      wait
      ;;
    rollup_seq_m|rollup_seq_n|rollup_seq_o|rollup_seq_p)
      chunks=4
      prev=$(rollup_of "$label_n")
      for i in 1 2 3 4; do
        post_chunk "$label_n" "$(new_biz)" "${key}-$i" 1 >/dev/null
        cur=$(rollup_of "$label_n")
        if [[ "$cur" -lt "$prev" ]]; then monotone=0; fi
        prev=$cur
      done
      ;;
    tri_fanout)
      chunks=12
      ( for i in 1 2 3 4; do post_chunk "$label_n" "$(new_biz)" "TF-N$i" 1 >/dev/null; done ) &
      ( for i in 1 2 3 4; do post_chunk "$label_e" "$(new_biz)" "TF-E$i" 1 >/dev/null; done ) &
      ( for i in 1 2 3 4; do post_chunk "$label_w" "$(new_biz)" "TF-W$i" 1 >/dev/null; done ) &
      wait
      ;;
    solo_west)
      chunks=4
      for i in 1 2 3 4; do post_chunk "$label_w" "$(new_biz)" "SW-$i" 1 >/dev/null; done
      ;;
    *) echo "unknown scenario $key" >&2; exit 2 ;;
  esac
  dup=$(count_dup_biz)
  db_total=$(psql_lane -At -c "SELECT COUNT(*) FROM line_slice;")
  accepted_total=$(psql_lane -At -c "SELECT COALESCE(SUM(accepted_lines),0) FROM lane_attempt;" 2>/dev/null || echo "$db_total")
  if [[ "$db_total" != "$accepted_total" ]]; then
    parity=0
    lost=$((lost + $(python3 -c "print(max(0, int('$accepted_total') - int('$db_total')))")))
  fi
  if [[ "$key" == "stamp_guard" || "$key" == "partial_abort" ]]; then
    lost=0
    parity=1
  fi
  dup=$(count_dup_biz)
  for fam in "$label_n" "$label_e" "$label_w"; do
    cap=$(psql_lane -At -c "SELECT cap_slots FROM partition_dim WHERE label='$fam';")
    act=$(active_of "$fam")
    if [[ "$act" -gt "$cap" ]]; then unstable=1; fi
  done
  python3 - <<PY
import json
print(json.dumps({
  "lost_rows": max(0, int("$lost")),
  "duplicate_external_keys": int("$dup"),
  "unstable_totals": bool(int("$unstable")),
  "chunks_attempted": int("$chunks"),
  "line_parity_ok": bool(int("$parity")),
  "rollup_monotone": bool(int("$monotone")),
  "read_after_write_ok": bool(int("$raw")),
}))
PY
}

run_case
'''

LIB = {
    "curl_wrap.sh": """#!/usr/bin/env bash
set -euo pipefail
API_BASE="http://127.0.0.1:8080"

api_post_batch() {
  local label="$1"
  local body="$2"
  curl -fsS -X POST "${API_BASE}/api/partition/${label}/batch" \
    -H 'Content-Type: application/json' \
    -d "${body}"
}

api_snapshot() {
  local label="$1"
  curl -fsS "${API_BASE}/api/partition/${label}/snapshot"
}

api_reset() {
  curl -fsS -X POST "${API_BASE}/api/admin/reset" >/dev/null || true
}
""",
    "psql_wrap.sh": """#!/usr/bin/env bash
set -euo pipefail
psql_lane() {
  psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-lane_db}" -v ON_ERROR_STOP=1 "$@"
}
""",
    "result_collect.sh": """#!/usr/bin/env bash
set -euo pipefail
emit_row() {
  python3 -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1])))' "$1"
}
""",
    "run_scenario.sh": RUN_SCENARIO_SH,
}

LANE_AUDIT = r'''#!/usr/bin/env bash
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
'''

DECOY_SQL = """\
-- nightly metrics snapshot (not on hot path)
CREATE TABLE IF NOT EXISTS metrics_n8f_snapshot (
  captured_at TIMESTAMPTZ PRIMARY KEY DEFAULT now(),
  payload JSONB NOT NULL
);
"""

from gen_java_batch_lane_api import API, DOCS, TEST_OUTPUTS  # noqa: E402
from gen_java_batch_lane_solve import LANE_FIX_PATCH, SOLVE_SH  # noqa: E402
