#!/usr/bin/env bash
set -euo pipefail

source /app/lib/redis_wrap.sh
source /app/lib/seed_helpers.sh

wait_redis
seed_catalog
