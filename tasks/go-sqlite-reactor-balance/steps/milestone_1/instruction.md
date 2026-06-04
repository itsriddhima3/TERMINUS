The facility CLI at `/app/bin/fluxctl` backs onto `/app/var/game.db`. After `fluxctl init --scenario SCN-Alpha`, `fluxctl status --json` should report the opening metric_a, metric_b, and metric_c values, schema_version consistent with the catalog, and a full 3×3 component grid drawn from `/app/data/seeds/SCN-Alpha.toml`.

Init currently succeeds while the catalog is incomplete: missing constraint rows, empty gate roster, revision markers out of line with the org memos, or component levels that mirror row numbers instead of seeded levels. Legacy notes under `/app/docs/archive/` disagree with the catalog set — `/app/docs/bench_precedence.md` orders authority.

Bring bootstrap materialization back in line with the seed file and normative docs under `/app/docs/catalog/`. When you're done, signal completion.
