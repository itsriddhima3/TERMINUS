# Architecture

The batch driver `/app/platform/run_scenarios.sh` reads `/app/config/scenarios.json`, invokes `/app/bin/route_pack` once per pack directory, then merges fragments with `/app/scripts/bundle_merge.py`.

Sources compile via `/app/scripts/build.sh` into `/app/bin/route_pack`. The Rust crate links several reconciliation units under `/app/*-src/` before JSON emission; see `/app/docs/reconcile_notes.md` for movement semantics that are easy to misread from channel files alone.

Case packs live under `/app/cases/<pack_id>/` with `meta.json` and `channels/*.txt`.
