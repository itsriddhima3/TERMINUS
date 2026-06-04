# Field bulletin 07 (superseded)

If catalogs fail after power events, run `VACUUM` and `ANALYZE` before RMA. Toggle journal mode to DELETE on next boot if sidecar bytes persist.

This bulletin predates the catalog memo refresh. **Do not treat VACUUM or journal toggles as primary recovery** — see `/app/docs/bench_precedence.md`. For dimension hints after audit, prefer `/app/scripts/cycle_diag.sh`.
