#!/bin/bash

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p1 -d /app < patches/m3_valuescale.patch
patch -p1 -d /app < patches/m3_quota.patch
patch -p1 -d /app < patches/m3_duty.patch
patch -p1 -d /app < patches/m3_report.patch
patch -p1 -d /app < patches/m3_reconcile_cmd.patch

bash /app/scripts/build-cli.sh
bash /app/scripts/start-api.sh
/app/bin/customsctl ingest SHIP-2024-Q1
/app/bin/customsctl enrich SHIP-2024-Q1
/app/bin/customsctl reconcile SHIP-2024-Q1
