#!/usr/bin/env bash
# Rebuild wirectl and emit the full audit report.
set -euo pipefail

cd /app
mkdir -p /app/bin /app/output

go build -o /app/bin/wirectl ./cmd/wirectl
exec /app/bin/wirectl \
  -matrix /app/data/scenario_matrix.json \
  -out /app/output/wire_audit.json
