# Ops bulletin 09 — vacuum advisory

Field teams reported smaller `.db` files after `VACUUM` on scenario catalogs that still showed incomplete `observed_rows`. Vacuum does not restore missing fact rows, does not reset `busy_events`, and does not change the effective journal family sqlite reports.

If ledgers show `delete` family strings, bulletin 09 does not apply — return to catalog part 01 (K2 dimension) and `bench_profiles.toml` `[m7]`.
