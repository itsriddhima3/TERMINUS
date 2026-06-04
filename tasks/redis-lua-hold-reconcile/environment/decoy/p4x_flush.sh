#!/usr/bin/env bash
# periodic TTL sweep for ancillary cache keys (decoy)
set -euo pipefail
source /app/lib/redis_wrap.sh
redis_cli KEYS 'cache:*' | while read -r k; do
  [[ -n "$k" ]] || continue
  redis_cli EXPIRE "$k" 3600 >/dev/null
done
