# Bench precedence

1. `/app/docs/ingest_contract.md`
2. `/app/docs/lane_matrix.md`
3. `/app/docs/catalog/part_00_rubric.md` then `part_01` through `part_03`
4. `/app/config/bench_profiles.toml` (numeric dimension stanzas)
5. `/app/docs/archive/legacy_journal_notes.md` (historical only)
6. `/app/docs/ops/bulletin_09.md` (advisory; does not override catalog)

Resolve implementation roots by reading `crate_root` for the dimension named in the rubric, not by searching for stress symptom strings inside source file names.
