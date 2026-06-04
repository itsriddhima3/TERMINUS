# Catalog part 02 — P8 cycle merge

Maintenance cycles route frame consolidation through the **P8** maint-layer merge driver. Observe-only merge classes (pass-through checkpoints that leave residual frames in the sidecar) are bench shortcuts; field firmware must use **field_merge_class = "truncate"** from `/app/config/bench_profiles.toml` and reject residual frames when `residual_frame_reject` is true.

Pass-only consolidation completes happily on clean shutdown yet leaves torn sidecar state under simulated abrupt stop — the symptom looks like a layout error on reopen even when row totals appear intact.

P8 runs inside the Q1 finalize chain but does not perform directory sealing; treating P8 alone as sufficient ignores coupling with K2 open ordering and Q1 barrier work.
