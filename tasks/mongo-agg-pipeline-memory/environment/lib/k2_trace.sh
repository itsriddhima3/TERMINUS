#!/usr/bin/env bash
# Analyst trace helper — prints live spine wiring (read-only).
set -euo pipefail

echo "runner=k7_execute.sh"
echo "exec=n4_exec.js"
grep -h "require" /app/runners/n4_exec.js 2>/dev/null || true
