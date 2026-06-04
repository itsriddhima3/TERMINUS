#!/bin/bash
# Builds the audit binary and installs it to /app/bin/audit.
set -euo pipefail

mkdir -p /app/bin
cd /app
go build -o /app/bin/audit ./cmd/audit
echo "Built /app/bin/audit"
