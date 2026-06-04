# Scoring profile

The final score for a session is composed from four ingredients
inside `Game\Reckon::compose`:

- `baseValue` — the per-challenge starting units (see `challenges.base_units` in the schema; 1000 for both seeded challenges).
- `discretePenalties` — sum of per-hint penalty units that were
  admitted as penalised by `Throttle::admit` during the session.
  A hint admitted as a "free" issue inside the rate bucket
  contributes 0 to this sum.
- `bonusUnits` — sum of per-match correctness bonus units for
  every mark that classified to a real region, plus the configured
  `hint_reveal_bonus` for every `hint` command issued during the
  session (including across pause/resume pairs).
- `elapsedSeconds` — wall-clock duration of the session in seconds
  (or the simulated equivalent when `--clock=scripted`).

The numeric weights for `discretePenalties`, `bonusUnits`, and
the per-second decay live in `config/scoring_profile.json`. The
composition contract is that the final integer published to the
`sessions.score` column is a monotonically non-increasing function
of additional hint draws within a fixed scenario — i.e. adding
one more hint command to an otherwise-identical play sequence
must never increase the published value.

Composition order (all terms integrated before quantisation):

1. Start from `baseValue`.
2. Subtract per-second decay for `elapsedSeconds`.
3. Subtract `discretePenalties` (sum of penalised hint draws).
4. Add `bonusUnits` — matched-mark rewards plus `hint_reveal_bonus`
   for every `hint` command on the session (the play loop aggregates
   this; do not drop reveal bonus when adjusting monotonicity).
5. Snap the resulting integer to `rounding_step` (round-half-up).

Quantising before penalties or bonuses land produces scores that are
not multiples of `rounding_step` and can rise when an extra penalised
hint is added. `Game\Wager` previews describe-mode estimates only;
closed-session persistence uses `Game\Reckon::compose`.

The `Sink::commit` step writes the composed value to
`sessions.score` and also serialises the per-component breakdown
to `sessions.component_breakdown` for debugging convenience.
