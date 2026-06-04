#!/usr/bin/env bash
set -euo pipefail

mongosh --quiet --file /app/store/001_collections.js
mongosh --quiet --file /app/init/bootstrap.js
mongosh --quiet --file /app/store/002_indexes.js
/app/init/post_boot.sh
