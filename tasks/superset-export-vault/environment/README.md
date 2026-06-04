# Superset export vault

Internal tooling for sealing BI export bundles before they leave the deployment perimeter.

Build:

```bash
bash /app/scripts/build.sh
```

Reference docs live under `/app/docs/` (`export_format.md`, `relay_fingerprint.md`, `envelope_slots.md`, `walker_policy.md`, `operations_notes.md`).

The audit harness at `/app/scripts/vault_audit.sh` is the acceptance path. Image build preloads offline pytest tooling under `/opt/uv-cache` (`UV_OFFLINE=1` at grade time). Auxiliary probes under `/app/lib/` and the staging quick-lane verifier are not graded.
