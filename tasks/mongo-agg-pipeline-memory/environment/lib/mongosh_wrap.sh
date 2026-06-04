#!/usr/bin/env bash
# Analyst-role mongosh wrapper (telemetry_db).
set -euo pipefail

mongosh "mongodb://127.0.0.1:27017/telemetry_db" "$@"
