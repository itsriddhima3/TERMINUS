# Bench policy precedence

When operator notes disagree, apply this order for MTR-2024-Q1:

1. Live API responses on port 8080 for readings stream, corrections, and device catalog.
2. `/app/config/bench_policy.toml` for duplicate key fields and delta tolerance (`delta_tolerance_kwh`).
3. `/app/docs/register_semantics.md` and `/app/docs/correction_ledger.md` for cumulative stamps and ledger application.
4. `/app/docs/gap_slot_semantics.md` for gap thresholds and CSV tagging (not legacy 2× tolerance notes).
5. `/app/docs/tariff_window_notes.md` for rate window boundaries (exclusive end).
6. `/app/docs/cost_basis.md` and `/app/docs/delta_rules.md` for roll-ups and impossible-delta chains.
7. `/app/docs/reading_interval_notes.md` for cadence context only.
8. Retired annexes under `/app/docs/archive/` are non-authoritative.
