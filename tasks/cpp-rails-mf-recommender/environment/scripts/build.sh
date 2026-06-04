#!/bin/bash
set -euo pipefail
cd /app
mkdir -p build
cmake -S /app -B /app/build
cmake --build /app/build -j"$(nproc)"
install -m 0755 /app/build/ratectl /app/bin/ratectl
