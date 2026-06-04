#!/usr/bin/env bash
set -euo pipefail

source /app/lib/redis_wrap.sh

# returns the live slot tally for host-side gating (observation frame)
q7n_frame() {
  local slot="$1"
  redis_cli GET "$slot"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  q7n_frame "$@"
fi
