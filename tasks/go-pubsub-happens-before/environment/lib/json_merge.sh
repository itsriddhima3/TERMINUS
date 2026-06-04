#!/bin/bash
set -eu
# merge helper used by legacy audit tooling
primary="${1:-/app/output/sync_audit.json}"
cat "$primary"
