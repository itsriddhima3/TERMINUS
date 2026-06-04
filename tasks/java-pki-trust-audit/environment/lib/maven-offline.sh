#!/bin/bash
set -euo pipefail
export MAVEN_OPTS="${MAVEN_OPTS:-}"
cd /app/cli
mvn -q -o -Dmaven.repo.local=/opt/m2 "$@"
