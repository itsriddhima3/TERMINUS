# overlay-inspect architecture

The CLI is a single-binary PHP application split across four top-level
package directories:

- `loop/` (`OverlayInspect\Cli`) — entrypoint dispatch, input parsing,
  output rendering. The `Loop` class drives the per-play command loop.
- `imaging/` (`OverlayInspect\Imaging`) — image acquisition (via the
  `MagickRunner` wrapper that shells out to `convert`), the
  `Stretch`/`Crop`/`Quantize` pipeline stages, and the coordinate
  helpers under `imaging/Coord` (`AffineWarp`, `Translate`).
- `game/` (`OverlayInspect\Game`) — gameplay logic. `PackLoader`
  materialises a challenge record from the database. `Overlap`
  classifies a player input cell against region polygons. `Throttle`
  mediates the rate bucket for hint admission and `Reckon` composes
  the final score from a base value, discrete penalties, bonus units,
  and elapsed seconds.
- `lifecycle/` (`OverlayInspect\Game\Lifecycle`) — `Lifecycle` hydrates
  engine state for new or resumed sessions.
- `persistence/` (`OverlayInspect\Persistence`) — `Connection` opens
  the SQLite handle, `Schema` materialises the schema if missing,
  `Tally` writes per-session event rows (marks and hints) with a
  rolling sequence number, and `Sink` writes the final composed score
  back to the `sessions` row. `Audit` is a separate administrative log
  used for init/vacuum events.

The boot path is `cli/overlay-inspect` → `Bootstrap::main()` →
`Loop::run()`. `Loop` constructs a `Lifecycle` instance per incoming
play subcommand and dispatches each stdin line to the relevant
collaborator: `mark` consults `Overlap` then notes via `Tally`, `hint`
consults `Throttle` then notes via `Tally`, `pause` flushes pending
writes and exits the per-play loop with a checkpoint, `resume`
re-enters via `Lifecycle::restoreFor`, and `quit` triggers
`Reckon::compose` + `Sink::commit`.

Supporting (non-play-path) modules live next to the fix-path classes
to keep the help-screen renderer, the `--describe` sub-command, and
the administrative tooling colocated with the play-path code they
parallel:

- `imaging/Pipeline/Crop.php`, `imaging/Pipeline/Quantize.php` —
  invoked from `--describe` for the histogram dump and the help
  preview.
- `imaging/Coord/Translate.php` — caption-text anchor alignment used
  by `--overlay-help`.
- `imaging/Coord/Polar.php` — arc layout used by the overlay-help
  help frame to render captions around region anchors.
- `game/Wager.php` — pre-play wager estimator used by `--describe`
  to preview the scoring profile; not the live score composer.
- `game/Gate.php` — per-day open-session admission gate
  (independent of the per-action rate bucket in `Throttle`).
- `lifecycle/Replay.php` — offline action-replay transcript used
  by `--describe` to print historic session traces.

None of these participate in the live `play` subcommand path. They
share vocabulary (`cellAspect`, `freeQuota`, `snap`, `tally->note`,
`bucket_start_ms`) with the play-path classes because they live in
the same domain, not because they belong on the gameplay code path.
