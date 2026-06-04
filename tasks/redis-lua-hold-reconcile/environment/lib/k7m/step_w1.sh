#!/usr/bin/env bash
set -euo pipefail

step_w1() {
  local label="$1"
  case "$label" in
    Alpha-Unit) echo "hold:alpha" ;;
    Beta-Crate) echo "hold:beta" ;;
    Gamma-Tote) echo "hold:gamma" ;;
    *) echo "hold:unknown" ;;
  esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  step_w1 "$@"
fi
