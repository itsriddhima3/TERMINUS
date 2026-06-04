# Ceremony data directory

Runtime database path: `/app/data/ceremonies.db`.

The SQLite file is created during the container image build by `scripts/init-db.sh`.
This directory is reserved for that database and any runtime artifacts the audit CLI writes.
