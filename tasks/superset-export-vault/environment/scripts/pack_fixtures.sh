#!/bin/bash
set -euo pipefail

export PATH="/usr/local/go/bin:${PATH}"

cd /app
go run ./cmd/packfixtures
