# Bench precedence

When catalog memos, archive notes, and field bulletins disagree, this document orders authority:

1. `/app/docs/catalog/part_01_open.md`, `/app/docs/catalog/part_02_cycle.md`, and `/app/docs/catalog/part_03_finalize.md`
2. `/app/config/bench_profiles.toml`
3. `/app/docs/storage_contract.md`
4. `/app/docs/compaction_window.md`
5. `/app/docs/archive/legacy_wal_notes.md`
6. `/app/docs/ops/field_bulletin_07.md`

Durability expectations for abrupt-stop recovery are defined in the catalog trilogy (K2, P8, Q1), not the archive layer or field bulletins.
