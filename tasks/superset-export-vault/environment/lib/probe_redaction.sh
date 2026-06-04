#!/bin/bash
set -euo pipefail

# Offline redaction probe — counts line-prefix password markers only.
# Does not exercise walk_q3; nested provider/replica paths may still leak.
for dir in /app/fixtures/*_export; do
  [ -d "$dir" ] || continue
  find "$dir/metadata" -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) -print0 2>/dev/null \
    | while IFS= read -r -d '' f; do
        grep -cE '^(password|secret):' "$f" 2>/dev/null || true
      done
done
