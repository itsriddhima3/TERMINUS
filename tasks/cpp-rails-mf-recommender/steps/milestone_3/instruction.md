Submission should load the pack, score every holdout pair from the service, POST the batch with the active bench id, and write `/app/output/submission/receipt.json`. Receipts come back rejected or with rmse above the bench cutoff (**0.85** for bench-split-a7) even when the pack header looks locally consistent. Missing bench id yields zero scored rows.

Receipt carries `schema_version` 1, `accepted`, `rmse`, and `n_scored` (57 for the bench holdout set). Posted scores need quarter-star granularity before the **1**–**5** clamp. Envelope rules are catalog memo 04.

Run `ratectl submit --pack /app/output/model/pack.bin --base http://127.0.0.1:4567`. Signal completion when the receipt shows acceptance.
