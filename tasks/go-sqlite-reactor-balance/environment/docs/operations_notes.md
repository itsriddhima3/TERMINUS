# Operations field bulletin (2024-Q4)

> Not authoritative. See `/app/docs/bench_precedence.md`. This bulletin captures noisy floor reports only.

## Symptom: permissive move acceptance

Several teams reindexed `rules` and ran `PRAGMA optimize` on `/app/var/game.db`. Move violations persisted. Display-only ordering from `/app/decoy/q3l` policy probes also failed to predict live rejects. Floor chatter blamed stale reads of `constraints` without restarting the CLI.

## Symptom: premature victory / streak loss on save

Teams toggled WAL `synchronous=NORMAL` and increased cache size. Dwell counter still dropped on named slot reload.

## Symptom: revision marker stuck at B1

Repeat init left revision B1 in `meta` while TOML preview utilities under `/app/decoy/n8f` still showed the expected layout.
