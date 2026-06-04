#!/bin/bash
set -euo pipefail
mkdir -p /app/bin
mkdir -p /opt/m2
cd /app/cli
mvn -q -o -Dmaven.repo.local=/opt/m2 package -DskipTests
install -m 0755 target/meter-cli.jar /app/bin/meterctl.jar
cat > /app/bin/meterctl <<'WRAP'
#!/bin/bash
exec java -jar /app/bin/meterctl.jar "$@"
WRAP
chmod +x /app/bin/meterctl
