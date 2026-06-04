# Chapter 05 — Invoke defaults

`/app/config/invoke_policy.json` supplies `spine_defaults.allow_disk_use` for WK-SPINE batch lanes.

Per-call options of `{}` inherit policy verbatim. Setting `allow_disk_use` to false while grouping the full store before selective predicates guarantees memory-limit aborts on lab replicas.

The invoke wrapper under `/app/r7/` merges policy before calling `aggregate()`. Editing display-only invoke modules under `/app/hub/` does not change live behavior.
