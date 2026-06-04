#!/bin/bash
set -euo pipefail

mkdir -p /app/bin /app/build

SRC_DIRS=(
  "/app/cli/src/main/kotlin"
  "/app/core/src/main/kotlin"
)

rm -f /app/build/sources.txt
for d in "${SRC_DIRS[@]}"; do
  if [ -d "$d" ]; then
    find "$d" -type f -name '*.kt'
  fi
done | sort > /app/build/sources.txt

kotlinc -jvm-target 1.8 @"$(printf '%s' /app/build/sources.txt)" -d /app/build/cli.jar

cat > /app/bin/wbaudit <<'EOF'
#!/bin/bash
set -euo pipefail
exec java -cp "/app/build/cli.jar:/usr/share/java/kotlin-stdlib.jar" app.Main "$@"
EOF

chmod +x /app/bin/wbaudit

