#!/bin/bash
set -euo pipefail
# Dependencies are baked at image build via npm ci; verify offline readiness.
test -f /app/node_modules/express/package.json
