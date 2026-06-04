#!/bin/bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
patch -p1 -d /app < patches/m1_schema.patch

bash /app/scripts/build.sh
rm -f /app/var/game.db
/app/bin/fluxctl init --scenario SCN-Alpha
