#!/bin/bash
set -euo pipefail
if curl -sf "http://127.0.0.1:8080/health" >/dev/null 2>&1; then
  exit 0
fi
JAR="/app/api/target/meter-api.jar"
if [ ! -f "$JAR" ]; then
  echo "meter api jar not found at $JAR" >&2
  exit 1
fi
nohup java -jar "$JAR" --server.address=127.0.0.1 --server.port=8080 >/tmp/meter-api.log 2>&1 &
for _ in $(seq 1 80); do
  if curl -sf "http://127.0.0.1:8080/health" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.1
done
echo "meter api failed to start" >&2
exit 1
