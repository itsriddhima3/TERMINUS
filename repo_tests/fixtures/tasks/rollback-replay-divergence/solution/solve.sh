#!/usr/bin/env bash
set -euo pipefail

cd /app

cmake -S /app -B /app/build -DCMAKE_BUILD_TYPE=Release \
  -DTB_TIMELINE_MODE=2 -DTB_REEXEC_MODE=2

cmake --build /app/build -j"$(nproc 2>/dev/null || echo 2)"

mkdir -p /app/bin
install -m 0755 /app/build/netplay_matrix /app/bin/netplay_matrix

mkdir -p /app/output
/app/bin/netplay_matrix --out /app/output --pack /app/data/seed_scenarios.json
