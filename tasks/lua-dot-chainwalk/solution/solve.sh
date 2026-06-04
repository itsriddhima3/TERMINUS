#!/bin/bash
set -euo pipefail

ORACLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r "${ORACLE_DIR}/patches" /app/patches/

cd /app
patch -p1 < patches/walk_fix.patch
patch -p1 < patches/bridge_fix.patch
patch -p1 < patches/pack_fix.patch
patch -p1 < patches/sweep_fix.patch
patch -p1 < patches/gate_fix.patch
patch -p1 < patches/pem_fix.patch

rm -rf /app/output
mkdir -p /app/output/marked
bash /app/platform/run_cases.sh
