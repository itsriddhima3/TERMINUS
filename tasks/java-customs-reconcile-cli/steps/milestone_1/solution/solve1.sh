#!/bin/bash

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p1 -d /app < patches/m1_ingest.patch
patch -p1 -d /app < patches/m1_hs.patch
patch -p1 -d /app < patches/m1_ccy.patch

bash /app/scripts/build-cli.sh
bash /app/scripts/start-api.sh
/app/bin/customsctl ingest SHIP-2024-Q1
