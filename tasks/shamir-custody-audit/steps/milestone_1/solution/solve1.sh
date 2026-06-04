#!/bin/bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p1 -d /app < patches/m1_query.patch

cd /app
go build -o /app/bin/audit ./cmd/audit
mkdir -p /app/output
/app/bin/audit --db /app/data/ceremonies.db --dossier /app/docs/ceremony-policy-v3.md --out /app/output/report.json
