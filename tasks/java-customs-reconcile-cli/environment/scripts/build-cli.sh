#!/bin/bash
set -euo pipefail
mkdir -p /app/bin
mkdir -p /opt/m2
cd /app/cli
mvn -q -o -Dmaven.repo.local=/opt/m2 package -DskipTests
install -m 0755 target/customs-cli.jar /app/bin/customsctl.jar
cat > /app/bin/customsctl <<'WRAP'
#!/bin/bash
exec java -jar /app/bin/customsctl.jar "$@"
WRAP
chmod +x /app/bin/customsctl
