#!/usr/bin/env bash
set -euo pipefail

source /app/lib/psql_wrap.sh

REGION_ID="${1:?region id}"
ZONE_CODE="${2:?zone code}"

tmp="$(mktemp)"
sed -e "s/__REGION__/${REGION_ID}/g" -e "s/__ZONE__/${ZONE_CODE}/g" /app/q/spine_template.sql >"$tmp"

{
  echo "EXPLAIN (FORMAT JSON)"
  cat "$tmp"
} >"${tmp}.explain"

psql_as_planner -f "${tmp}.explain" -t -A >"${tmp}.plan"
cat "${tmp}.plan"
rm -f "$tmp" "${tmp}.explain" "${tmp}.plan"
