#!/usr/bin/env bash
set -euo pipefail

/usr/local/bin/docker-entrypoint.sh redis-server /app/config/redis.conf.snippet --daemonize yes
until redis-cli PING 2>/dev/null | grep -q PONG; do
  sleep 0.1
done
/app/init/post_boot.sh
exec "$@"
