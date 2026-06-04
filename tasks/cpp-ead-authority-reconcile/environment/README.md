# ARC batch reconciliation

Single-container workspace: Express authority API plus `arcctl` C++ CLI. Dependencies are baked at image build; runtime works offline (`allow_internet = false`).

```bash
/app/scripts/start-api.sh
/app/scripts/build-cli.sh
/app/bin/arcctl parse ARC-2024-Q2
/app/bin/arcctl link ARC-2024-Q2
/app/bin/arcctl report ARC-2024-Q2
```

Documentation under `/app/docs/`.
