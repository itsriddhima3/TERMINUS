#!/usr/bin/env bash
set -euo pipefail
cd /app
go build -o /app/bin/wirectl ./cmd/wirectl
exec /app/bin/wirectl -matrix /app/data/scenario_matrix.json -scenario scenario_c -out /app/output/wire_audit.json
