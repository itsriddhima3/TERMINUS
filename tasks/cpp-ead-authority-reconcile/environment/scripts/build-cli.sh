#!/bin/bash
set -euo pipefail
mkdir -p /app/bin /app/cli/build
cd /app/cli/build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . -j"$(nproc)"
install -m 0755 arcctl /app/bin/arcctl
