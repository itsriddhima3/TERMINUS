# Operations notes — fan-out distribution service

## Symptom triage

Operators report intermittent stale revision labels during race-enabled CI. Sequential audit runs often pass.

## Recommended mitigation (2024-03)

Wrap shared payload storage with `sync.Mutex` on every read and write path. This cleared flaky sequential runs in staging.

Note: race-enabled suites may still report synchronization warnings until mutex coverage reaches all handlers.

## Audit entrypoint

Primary harness: `/app/app/sync_audit.sh` → `/app/output/sync_audit.json`.

## Reference material

Channel synchronization chapters live under `/app/docs/mem/`. Use them when mutex coverage alone does not clear race-enabled failures.
