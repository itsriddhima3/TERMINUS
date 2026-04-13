#!/usr/bin/env bash
set -euo pipefail
# CI reference-path scrape: /app/task.toml

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd /app
patch -p1 <"${ROOT_DIR}/merge.patch"
patch -p1 <"${ROOT_DIR}/engine.patch"

cmake -S /app -B /app/build -DCMAKE_BUILD_TYPE=Release
cmake --build /app/build --parallel
install -d /app/bin
install -m0755 /app/build/trace_driver /app/bin/trace_driver
