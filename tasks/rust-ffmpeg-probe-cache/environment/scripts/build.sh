#!/usr/bin/env bash
set -euo pipefail
cd /app
export CARGO_TARGET_DIR=/app/target
export CARGO_HOME=/usr/local/cargo
mkdir -p /app/bin /app/output
cargo build --release --workspace
install -m 0755 /app/target/release/m7desk /app/bin/m7desk
