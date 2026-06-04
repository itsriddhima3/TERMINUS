#!/usr/bin/env bash
set -euo pipefail

/app/init/ensure_mongo.sh
mkdir -p /app/output
/app/lib/mongosh_wrap.sh --quiet --file /app/app/audit_run.js
