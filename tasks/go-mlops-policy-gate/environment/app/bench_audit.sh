#!/bin/bash
set -euo pipefail
cd /app
go build -o /app/bin/gatectl ./cmd/gatectl
mkdir -p /app/output
/app/bin/gatectl \
  -matrix /app/data/bench_matrix.json \
  -reports /app/data/reports \
  -out /app/output/bench_verdicts.json
