#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:${PATH}"

cd /app
bash /app/scripts/pack_fixtures.sh
go build -o /app/bin/vaultctl ./cmd/vaultctl
