#!/usr/bin/env bash
# /app/scripts/init_workspace.sh — prepare writable state directory.
set -euo pipefail

mkdir -p /app/var
chmod 0777 /app/var

if [ ! -f /app/var/game.db ]; then
  : > /dev/null
fi

echo "workspace ready: /app/var"
