#!/bin/bash
set -euo pipefail
curl -sf http://127.0.0.1:4567/api/v1/split | head -c 200
echo
