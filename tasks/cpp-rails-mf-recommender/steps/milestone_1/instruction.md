The C++ operator CLI at `/app/bin/ratectl` should pull training rows from the local Rack service on port 4567 and materialize `/app/output/splits/manifest.json` plus `/app/output/splits/train.jsonl`. Fetch currently finishes early: manifest `n_train` does not match downloaded lines, `train_sha256` disagrees with a second pass, holdout pairs appear in the jsonl cache, or fit hyperparameters copied from the split envelope drift from bench values.

Manifest uses `schema_version` 1 and must record `split_id`, user/item counts (`n_users` 24, `n_items` 32, `n_train` 504 for bench-split-a7), fit hyperparameters from the split response, and a hex `train_sha256` over the jsonl body. Cached training star values stay within **1** through **5**. Org memos under `/app/docs/catalog/` disagree with `/app/docs/archive/` — `/app/docs/bench_precedence.md` orders authority.

Run `ratectl fetch --base http://127.0.0.1:4567`. When you're done, signal completion.
