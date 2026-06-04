#!/bin/bash
set -euo pipefail

DB_PATH="${DB_PATH:-/app/state/challenges.db}"
SEED_SQL="${SEED_SQL:-/app/assets/seed/seed_pack.sql}"

mkdir -p "$(dirname "$DB_PATH")"

if [ -f "$DB_PATH" ]; then
    rm -f "$DB_PATH" "$DB_PATH-wal" "$DB_PATH-shm"
fi

sqlite3 "$DB_PATH" < "$SEED_SQL"

php -r "
\$pdo = new PDO('sqlite:$DB_PATH');
\$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
\$pdo->exec('PRAGMA foreign_keys = ON;');
echo 'seed db rows in packs: ' . \$pdo->query('SELECT count(*) FROM packs')->fetchColumn() . PHP_EOL;
echo 'seed db rows in challenges: ' . \$pdo->query('SELECT count(*) FROM challenges')->fetchColumn() . PHP_EOL;
echo 'seed db rows in region_defs: ' . \$pdo->query('SELECT count(*) FROM region_defs')->fetchColumn() . PHP_EOL;
"
