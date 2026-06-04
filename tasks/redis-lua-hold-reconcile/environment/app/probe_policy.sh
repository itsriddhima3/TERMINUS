#!/usr/bin/env bash
# read-only policy dump for dashboards
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
print(Path("/app/config/worker_policy.toml").read_text())
PY
