# Session states

A session row in the `sessions` table moves through three states:

1. **fresh** — opened by `Lifecycle::freshFor(<challenge-id>)`;
   `opened_at_ms` set, `closed_at_ms` NULL, `closed_reason` NULL.
2. **open after pause** — entered when the play loop processes a
   `pause` command; the row remains with `closed_at_ms` NULL and
   `closed_reason` set to the literal string `paused`. Pending
   writes are flushed before the loop exits.
3. **closed** — entered when the play loop processes a `quit`
   command or when the player exits cleanly; `closed_at_ms` set,
   `closed_reason` set to `quit`, and `score` is populated by
   `Sink::commit`.

A new `play` invocation against the same challenge inspects the
existing rows first: if a row exists with `closed_reason = 'paused'`
the engine calls `Lifecycle::restoreFor(<row-id>)` to hydrate
the in-memory tally seed from the database, then re-enters the
play loop. Otherwise it calls `Lifecycle::freshFor(<challenge-id>)`.

`Tally::snapshot(<row-id>, <kind>)` returns the highest
`sequence_no` ever written for a given (session, kind) tuple
and is used by `Lifecycle` to seed the in-memory rolling
counter; subsequent `Tally::note(...)` calls increment that
counter monotonically.
