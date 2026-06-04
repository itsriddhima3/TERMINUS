#!/bin/bash
set -euo pipefail

OUT_DIR="${OUT_DIR:-/app/docs/review}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "${SCRIPT_DIR}/gen_transcript.py" "${OUT_DIR}"
