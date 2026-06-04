#!/bin/bash
set -euo pipefail
mkdir -p /app/bin /app/output
cd /app/cli
mvn -q -Dmaven.repo.local=/opt/m2 package -DskipTests
install -m 0755 target/trust-audit-cli.jar /app/bin/trustaudit.jar
cat > /app/bin/trustaudit <<'WRAP'
#!/bin/bash
exec java -jar /app/bin/trustaudit.jar "$@"
WRAP
chmod +x /app/bin/trustaudit
