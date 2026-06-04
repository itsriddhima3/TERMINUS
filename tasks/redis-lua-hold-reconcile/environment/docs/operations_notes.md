# Operations bulletin

Parallel grant lanes occasionally overshoot caps in staging. Changes tried so far:

- Raised retry backoff in worker policy
- Increased client timeouts
- Switched dispatch to registry archive entries for cold-path tooling

Burst audit rows still show overshoot while solo rows pass. See `/app/docs/bench_precedence.md` for documentation precedence.
