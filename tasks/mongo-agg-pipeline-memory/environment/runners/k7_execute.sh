#!/usr/bin/env bash
set -euo pipefail

/app/init/ensure_mongo.sh
/app/lib/mongosh_wrap.sh --quiet --file /app/runners/n4_exec.js
