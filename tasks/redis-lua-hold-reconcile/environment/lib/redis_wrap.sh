#!/usr/bin/env bash
set -euo pipefail

REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"

redis_cli() {
  redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "$@"
}

wait_redis() {
  local tries=120
  while (( tries > 0 )); do
    if redis_cli PING 2>/dev/null | grep -q PONG; then
      return 0
    fi
    sleep 0.1
    tries=$((tries - 1))
  done
  return 1
}
