#!/usr/bin/env bash
set -euo pipefail
source /app/init/bootstrap_once.sh
source /app/lib/redis_wrap.sh
wait_redis
