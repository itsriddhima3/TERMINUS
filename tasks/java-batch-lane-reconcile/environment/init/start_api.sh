#!/usr/bin/env bash
set -euo pipefail
source /app/init/ensure_pg.sh
export SPRING_CONFIG_LOCATION="file:/app/api/application.yml,file:/app/api/application-prod.yml"
export SPRING_FLYWAY_LOCATIONS="filesystem:/app/db/migration"
if [[ -f /var/run/lane-api.pid ]]; then
  if kill -0 "$(cat /var/run/lane-api.pid)" 2>/dev/null; then
    exit 0
  fi
fi
# When sourced, use return — callers invoke via bash.
nohup java -jar /app/api/lane-api.jar > /app/output/api.log 2>&1 &
echo $! > /var/run/lane-api.pid
for i in $(seq 1 120); do
  if curl -fsS http://127.0.0.1:8080/actuator/health >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.5
done
echo "API failed to become healthy" >&2
exit 1
