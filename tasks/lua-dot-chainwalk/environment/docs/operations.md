# Operations

Authoritative references for auditors:

- `/app/docs/audit_clock.md` — wall clock basis (`TZ_BASE`) vs GMT cert dates
- `/app/docs/verify_chain.md` — OpenSSL verify flag order
- `/app/docs/edge_legend.md` — edge families, `serves` expansion, deny direction

Regenerate PEM fixtures:

```bash
bash /app/scripts/regen_cases.sh
```

Run full audit sweep:

```bash
bash /app/platform/run_cases.sh
```

Health probe (OpenSSL + Lua present):

```bash
bash /app/platform/health_probe.sh
```
