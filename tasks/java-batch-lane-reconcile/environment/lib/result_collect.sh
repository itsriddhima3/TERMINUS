#!/usr/bin/env bash
set -euo pipefail
emit_row() {
  python3 -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1])))' "$1"
}
