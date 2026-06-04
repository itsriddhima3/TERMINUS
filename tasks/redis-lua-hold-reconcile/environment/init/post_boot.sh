#!/usr/bin/env bash
set -euo pipefail

# post container boot marker
: > /app/init/.post_boot_ok
