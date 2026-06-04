# Architecture

> **Legacy note (pre-2024 sketches):** Harbor exports often drew both `trusts` and `issued_by` edges. Older walk helpers defaulted to `issued_by` closure because operators believed issuer metadata matched reachability. Current pack audits follow the edge-family rules in `edge_legend.md`.

```
platform/chainwalk     -> invokes platform sweep
platform/run_cases.sh  -> registry loop, bundle write
flow-src/run_*.lua     -> per-pack orchestration (CR8: <=2 fix imports each)
graph-src/walk.lua     -> op_walk_a closure
openssl-src/bridge.lua -> reconcile_b fingerprints
policy-src/gate.lua    -> phase_c row verdict fold
emit-src/paint.lua     -> marked DOT writer
pem-src/load.lua       -> PEM path resolution from sketch attrs
decoy-src/*            -> layout metrics only
```

Data roots: `/app/cases/<pack_id>/layout.dot` plus `certs/*.pem`.
