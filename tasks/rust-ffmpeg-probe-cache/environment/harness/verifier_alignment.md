Verifier-side helpers (not part of the desk binary) may parse `/app/data/stress_manifest.toml` with a TOML loader and recompute `ledger_digest` with SHA-256 over the pre-final JSON body described in ingest_contract.md.

The verifier may run `m7desk run-stress` with a harness ledger at `/tmp/vr_stress_ledger.json` before comparing against `/app/output/stress_ledger.json`. Rerun smoke paths such as `/tmp/vr_stress_rerun.json` are harness-only outputs.
