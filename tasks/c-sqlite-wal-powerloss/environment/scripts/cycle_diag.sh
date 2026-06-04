#!/usr/bin/env bash
# Emits per-scenario dimension hints after audit — compare to bench_profiles.toml.
set -euo pipefail

WORKDIR="${1:-/tmp/datalog_audit}"
PROFILES="/app/config/bench_profiles.toml"

if [[ ! -d "$WORKDIR" ]]; then
  echo "cycle_diag: missing workdir $WORKDIR" >&2
  exit 1
fi

k2_expect="$(awk -F= '/^field_sync_class/{gsub(/ /,"",$2); print $2}' "$PROFILES")"
p8_expect="$(awk -F= '/^field_merge_class/{gsub(/[ "]/,"",$2); print $2}' "$PROFILES")"
stamp="$(awk -F= '/^sync_stamp_name/{gsub(/[ "]/,"",$2); print $2}' "$PROFILES")"

echo "cycle_diag: workdir=$WORKDIR expect_k2_class=$k2_expect expect_p8_merge=$p8_expect expect_stamp=$stamp"
found=0
for db in "$WORKDIR"/*.db; do
  [[ -f "$db" ]] || continue
  base="$(basename "$db" .db)"
  [[ "$base" == *"_probe" ]] && continue
  found=1
  sync="$(sqlite3 "$db" 'PRAGMA synchronous;')"
  jmode="$(sqlite3 "$db" 'PRAGMA journal_mode;')"
  wal_bytes=0
  if [[ -f "${db}-wal" ]]; then
    wal_bytes="$(stat -c%s "${db}-wal" 2>/dev/null || echo 0)"
  fi
  shm_bytes=0
  if [[ -f "${db}-shm" ]]; then
    shm_bytes="$(stat -c%s "${db}-shm" 2>/dev/null || echo 0)"
  fi
  stamp_ok=0
  if [[ -f "$WORKDIR/$stamp" ]] && [[ -s "$WORKDIR/$stamp" ]]; then
    stamp_ok=1
  fi
  k2_ok=0
  [[ "$sync" == "$k2_expect" ]] && k2_ok=1
  p8_ok=0
  [[ "$wal_bytes" -eq 0 && "$shm_bytes" -eq 0 ]] && p8_ok=1
  echo "  scenario=$base k2_dim=$k2_ok p8_dim=$p8_ok q1_dim=$stamp_ok sync=$sync jmode=$jmode wal_bytes=$wal_bytes shm_bytes=$shm_bytes"
done
if [[ "$found" -eq 0 ]]; then
  echo "cycle_diag: no scenario catalogs present — run audit first" >&2
  exit 1
fi
