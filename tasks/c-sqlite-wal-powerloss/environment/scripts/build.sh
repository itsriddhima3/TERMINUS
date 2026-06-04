#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p build bin

if [[ ! -f sqlite/sqlite3.c ]]; then
  echo "build.sh: missing /app/sqlite amalgamation (offline image required)" >&2
  exit 1
fi

make -j"$(nproc)" all
if [[ -f bin/datalog ]]; then
  chmod 0755 bin/datalog
fi
