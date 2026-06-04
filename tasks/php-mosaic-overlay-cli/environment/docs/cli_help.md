# overlay-inspect CLI help

## Top-level subcommands

```
php /app/cli/overlay-inspect play <challenge-id> [<resume-session-row-id>]
php /app/cli/overlay-inspect list
php /app/cli/overlay-inspect describe <challenge-id>
php /app/cli/overlay-inspect overlay-help
php /app/cli/overlay-inspect reset
```

`play` is the interactive subcommand: it drives an inspection
session against the named challenge and reads one whitespace-tokenised
command per line from stdin. The other subcommands are read-only
utilities for inspecting the seeded pack (or, in the case of `reset`,
purging session/mark/hint/audit rows for a clean test run).

## play command grammar

Each line on stdin is one command. Whitespace separates the verb
from its arguments. Unknown verbs emit `unknown command` on stderr
and are skipped.

| verb   | arguments     | effect                                                                                                                  |
|--------|---------------|-------------------------------------------------------------------------------------------------------------------------|
| `look` | -             | re-render the current scene to stdout                                                                                   |
| `mark` | `<col> <row>` | record a player mark at terminal cell (col, row); classified against scene regions                                      |
| `hint` | -             | request a hint; may incur a penalty depending on rate bucket                                                            |
| `tick` | `<ms>`        | (scripted clock only) advance the simulated clock by ms                                                                 |
| `pause`| -             | flush pending writes and exit play loop with a checkpoint; sets `closed_reason='paused'`                                |
| `quit` | -             | finalise the score, write to sessions row, close session with `closed_reason='quit'`                                    |

If `play` is invoked with a second positional argument, it is treated
as a `session_row_id` to resume; the lifecycle restores the existing
session's accumulated tallies and bucket window instead of opening a
fresh session.

## scripted clock

The CLI supports a deterministic clock mode for tests, enabled by
setting `SCRIPTED_CLOCK=1` in the environment before invoking `play`.
In that mode, the engine clock starts at 0 (or at the prior session's
`closed_at_ms` on resume) and only advances when the play loop
processes an explicit `tick <ms>` command. Out-of-mode, the engine
reads wall time from `microtime()` on every iteration.

## developer flags

Set in `/app/config/runtime.ini`:

- `echo_log`              — emit one line per accepted command to stdout
- `component_breakdown`   — print the JSON score component breakdown on close
