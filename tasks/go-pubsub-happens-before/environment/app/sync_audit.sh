#!/bin/bash
set -euo pipefail
OUT="/app/output/sync_audit.json"
mkdir -p /app/output
cd /app
go build -o /app/bin/scenar ./cmd/scenar
exec /app/bin/scenar --out "$OUT"
