#!/usr/bin/env bash
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
