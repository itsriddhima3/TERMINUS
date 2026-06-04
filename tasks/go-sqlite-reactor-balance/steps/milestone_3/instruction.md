Tick-driven play should advance metrics, count stable dwell in stable_streak, set won or lost correctly, and round-trip named slots through save/load including cell levels. Transcript replay via `fluxctl run` uses `/app/data/transcripts/`.

In-band metrics no longer lead to victory, saves drop dwell or tick state, and loss sometimes tracks band ceilings instead of breach cutoffs. Operator summaries in `/app/docs/win_conditions.md` defer to the catalog memos on outcome and archive semantics.

Fix outcome evaluation and session persistence so `/app/data/transcripts/win_alpha.script` finishes with won true at the required stable_streak, illegal transcripts fail, and mid-run save/load can resume a winning path. When you're done, signal completion.
