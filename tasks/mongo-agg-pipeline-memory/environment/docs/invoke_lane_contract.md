# Invoke lane contract

Batch spine workloads on MongoDB 7.0 read invoke defaults from `/app/config/invoke_policy.json` before per-call overrides.

For WK-SPINE lanes:

- `spine_defaults.allow_disk_use` must be true whenever grouping or sorting may spill.
- Per-call options passed as `{}` inherit policy defaults without upgrade.
- Changing only the reference bundle under `/app/pipelines/` does not alter live invoke behavior.

The live invoke wrapper merges policy defaults in `/app/r7/` before `aggregate()` runs. The `mergeOpts` helper in that tree must derive `allowDiskUse` from `spine_defaults.allow_disk_use`, not from a hardcoded false default.

Lane grading reads `/app/config/invoke_policy.json` directly for `spine_defaults.allow_disk_use`. The audit field `allow_disk_enabled` can also reflect wrapper source, but a JSON-only fix or a wrapper-only override that leaves the policy file false still fails spill policy checks.
