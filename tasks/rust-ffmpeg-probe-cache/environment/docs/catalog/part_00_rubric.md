# Dimension rubric (stress failures)

Map harness symptoms to catalog parts using the **dimension** field in `/app/config/bench_profiles.toml`. Do not treat a single symptom as proof for one crate — dimensions interact.

| Symptom cluster | Primary dimension | Secondary |
|-----------------|-------------------|-----------|
| Ledger `journal_mode` is `delete` or not `wal` while rows exist | K2 (part 01) | Q3 |
| `observed_rows` low, `busy_events` low, stderr quiet | Q3 (part 02) | K2 |
| `observed_rows` low or harness abort, `busy_events` high, stderr lock text | P2 (part 03) | Q3 |
| `integrity_ok` false after partial ingest | Q3 then K2 | P2 |
| Second `run-stress` pass regresses row totals | Q3 | K2 |

K2, Q3, and P2 numeric requirements are authoritative in `bench_profiles.toml` for their respective `[m7]`, `[q3]`, and `[p2]` stanzas. Part prose explains coupling only.
