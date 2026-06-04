#!/usr/bin/env bash
set -euo pipefail
source /app/lib/curl_wrap.sh
source /app/lib/result_collect.sh
exec /app/lib/run_scenario.sh "sibling_contention"
