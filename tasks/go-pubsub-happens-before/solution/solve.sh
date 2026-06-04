#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
patch -p0 -d /app < "$SCRIPT_DIR/sync-hub.patch"

cd /app
go build -o /app/bin/scenar ./cmd/scenar
go build -o /app/bin/daemon ./cmd/daemon
bash /app/app/sync_audit.sh
go test -race ./...
