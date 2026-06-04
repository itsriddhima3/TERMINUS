#!/usr/bin/env bash
# /app/scripts/build.sh — rebuild /app/bin/line_audit from /app sources.
set -euo pipefail

# Mixed Rust/Go link step: CGO_ENABLED=1 binds the Go binary to libsync_core.a.
export PATH="/usr/bin:/usr/local/go/bin:${PATH}"
export CGO_ENABLED=1

mkdir -p /app/bin
cd /app/sync_core
cargo build --release --locked
cd /app
GOFLAGS=-mod=mod go build -trimpath -buildvcs=false -o /app/bin/line_audit ./cmd/line_audit
