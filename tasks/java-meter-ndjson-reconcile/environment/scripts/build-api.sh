#!/bin/bash
set -euo pipefail
mkdir -p /opt/m2
cd /app/api
mvn -q -o -Dmaven.repo.local=/opt/m2 package -DskipTests
