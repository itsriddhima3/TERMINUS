# shamir-custody-audit

Audit tool for Shamir secret-sharing recovery ceremonies. Reads custody records from a SQLite database, validates submitted shares against quorum and role-separation rules from the ceremony policy dossier, reconstructs secrets via Lagrange interpolation over GF(2^8), and emits a structured JSON report.

## Usage

```
/app/bin/audit --db /app/data/ceremonies.db --dossier /app/docs/ceremony-policy-v3.md --out /app/output/report.json
```

## Build

```
cd /app
go build -o /app/bin/audit /app/cmd/audit
```

## Project layout

```
cmd/audit/          CLI entry point
internal/ledger/    SQLite query layer
internal/recovery/  GF(2^8) Shamir reconstruction
internal/policy/    Policy rule evaluation
internal/report/    JSON report writer
docs/               Ceremony policy dossier
configs/            Runtime configuration
scripts/            Database initialisation and build helpers
```
