#!/usr/bin/env bash
# /app/scripts/build.sh — rebuild /app/bin/fluxctl from /app sources.
set -euo pipefail

export PATH="/usr/bin:/usr/local/go/bin:${PATH}"
export CGO_ENABLED=1

mkdir -p /app/bin
cd /app
GOFLAGS=-mod=mod go build -trimpath -buildvcs=false -o /app/bin/fluxctl ./cmd/fluxctl
GOFLAGS=-mod=mod go build ./decoy/...
