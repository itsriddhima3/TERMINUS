### Decision
GO — Attempt 1. Milestone-scaffolded C++/Ruby ratings pipeline with local Rack API, paginated fetch, deterministic biased MF training, int8 pack artifact, and holdout submission; opaque fix symbols across three client roots; twenty-four verifier tests split by milestone with flipping-point coverage.

### Metadata
- version: 2
- Task name: cpp-rails-mf-recommender
- Title: Rails MF Recommender CLI
- Category: machine-learning
- Languages: ["cpp", "ruby", "bash", "sql"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["api_integration", "tool_specific"]
- Tags: ["cpp", "ruby", "matrix-factorization", "cli", "sqlite"]
- Milestones: 3

## Authoring Brief

### Public contract
Operators run `/app/bin/ratectl` against the local ratings service at `http://127.0.0.1:4567`. Milestone 1: `ratectl fetch --base http://127.0.0.1:4567` must write `/app/output/splits/manifest.json` (schema_version 1, split_id, n_users, n_items, n_train, train_sha256) and `/app/output/splits/train.jsonl` containing every training row from the paginated `/api/v1/train_ratings` endpoint. Milestone 2: `ratectl train --manifest /app/output/splits/manifest.json` must produce `/app/output/model/pack.bin` — a reproducible binary artifact with header fields documented under `/app/docs/catalog/` including global mean, fixed seed 42, int8 latent blocks with per-row scales, and train_sha256 matching the manifest. Milestone 3: `ratectl submit --pack /app/output/model/pack.bin --base http://127.0.0.1:4567` must POST dequantized scores for all holdout pairs to `/api/v1/predictions` and write `/app/output/submission/receipt.json` with `accepted` true and validation rmse at or below the service threshold. Bench precedence: `/app/docs/bench_precedence.md` overrides `/app/docs/archive/`.

### Failure topology
Symptoms cluster in three layers. Fetch reports success but train.jsonl row counts fall short of split metadata or checksum disagrees with manifest. Training emits a pack whose header seed, mean, or train_sha256 drift from manifest values, or latent blocks decode to wrong dot products. Submission returns rejected receipts or rmse above the service cutoff despite a locally consistent pack. The codebase presents as a conventional C++ CLI plus Ruby Rack ratings API with decoy pagination and quantize helpers; real defects sit in HTTP pagination termination, SGD bias/latent update coupling, int8 scale encoding, and holdout payload shaping.

### Environment shape
Dockerized workspace at `/app`: Ruby Rack service under `/app/service/` backed by SQLite, C++ `ratectl` entrypoint, opaque modules `k3p` (remote pull), `r7n` (fit loop), `m4t` (binary pack), `p1v` (remote emit), decoy modules, catalog docs, seed database, bash build/start helpers. Milestone tests invoke CLI subprocesses, parse JSON manifests/receipts, and inspect pack headers plus API-side rmse.

### Required artifacts
Milestone layout: `task.toml` with three `[[steps]]`, shared `environment/` (20+ files), `steps/milestone_N/{instruction.md, tests/{test.sh, test_mN.py}, solution/{solve.sh, solveN.sh, patches/}}`, root `output_contract.toml`.

### Test plan
Milestone 1 (8 tests): manifest schema_version; train row count matches split n_train; train_sha256 stable; sorted user/item coverage; pagination exhausts all pages; duplicate fetch idempotent checksum; manifest split_id matches API; no holdout rows in train.jsonl.
Milestone 2 (8 tests): pack magic/version; header seed 42; header train_sha256 matches manifest; global mean within tolerance of train mean; pack fingerprint stable across reruns; latent dim matches catalog; dequant dot sanity on sample pair; bias vectors non-zero.
Milestone 3 (8 tests): receipt accepted true; rmse at or below threshold; receipt schema_version; n_scored equals holdout count; resubmit idempotent; local holdout rmse matches receipt; pack round-trip score range 1-5; service stores no training rows in holdout table leak check.

### Drafting guardrails
Instructions stay symptoms-only per step: no C++ symbol names, no SGD formula, no int8 scale formula, no page parameter names beyond observable symptoms, no oracle command sequences. Fix-path symbols opaque (`op_fetch`, `phase_fit`, `step_q2`, `emit_v3`). Code symbols must not echo instruction nouns. Decoy modules perform genuine ancillary reads.

### Hard calibration (≤20% target)

**Deep domain expertise:** Org catalog memos reframe standard MF/SGD/pagination as lane ceilings, band scales, wire offset bytes, quarter-star POST quantization, and epoch-shuffle keyed `fit_seed + epoch`. Archive memos prescribe wrong truncating division, global scales, file-order visits, and `rows`/`items` aliases.

**Complex multi-step reasoning (10+ steps):** Typical repair: bench precedence → catalog INDEX → memos 01–05 + examples → trace split API → fix lane pull (response ceiling + canonical array key + manifest hyperparams) → fix fit loop (manifest hyperparams, shuffle, lr decay, offsets) → fix pack (per-row scale, 32-char digest, wire +128) → fix submit (split_id, predictions, wire decode, quarter clamp).

**Subtle debugging:** Truncated local ceiling drops final lane; file-order training passes fingerprint stability only after shuffle fix; global scale passes magic check but fails wire-offset test; missing split_id yields accepted=false with n_scored=0 despite locally sane scores.

**Niche stack:** C++17 + libcurl + Ruby Rack + SQLite + custom binary pack + offset-binary quantization.

**Disclosure control:** Instructions symptoms-only; normative rules scattered across five catalog memos with misleading archive counterparts.

### Triviality Ledger

- Truncating local lane ceiling passes most pages but fails lane-ceiling-thirty and manual parity tests.
- Fixing array key alone still misses final lane when ceiling is locally recomputed.
- File-order training with constant lr passes mean check but fails fingerprint and rmse tests after shuffle/decay fix.
- Global band scale passes magic check but fails wire-offset and on-disk size tests.
- Raw int8 wire bytes without +128 offset pass dot sanity on some rows but fail wire-offset and submit rmse tests.
- POST with predictions key but no split_id scores zero rows despite plausible scores.

### Per-gate Pitfall Inventory

- RC1 — Oracle patches touch pull, fit loop, pack, and submit modules; not a one-file revert.
- RC6 — Milestone instructions describe observable drift, not fix sites or algorithms.
- RC7 — Combined solve scripts apply substantive C++ patches ≥40 LOC semantic delta.
- CR2 — Flipping contract splits k3p, r7n, m4t/p1v across 8+8+8 tests (max ratio 8/24).
- CR7 — Instruction nouns banned from fix-path identifiers (rating, matrix, latent, quantize, etc.).
- GX9 — split_id, seed 42, schema_version 1, rmse threshold grounded in instructions/docs before tests assert them.
- Static checks — Milestone test_mN.py classes, per-step test.sh, no root-level instruction/tests/solution.

### Initial Draft Commitments

- `tasks/cpp-rails-mf-recommender/task.toml`
- `tasks/cpp-rails-mf-recommender/output_contract.toml`
- `tasks/cpp-rails-mf-recommender/environment/Dockerfile`
- `tasks/cpp-rails-mf-recommender/environment/.dockerignore`
- `tasks/cpp-rails-mf-recommender/environment/CMakeLists.txt`
- `tasks/cpp-rails-mf-recommender/environment/cmd/ratectl/main.cpp`
- `tasks/cpp-rails-mf-recommender/environment/client/k3p/pull.cpp`
- `tasks/cpp-rails-mf-recommender/environment/client/k3p/pull.h`
- `tasks/cpp-rails-mf-recommender/environment/core/r7n/loop.cpp`
- `tasks/cpp-rails-mf-recommender/environment/core/r7n/loop.h`
- `tasks/cpp-rails-mf-recommender/environment/core/m4t/pack.cpp`
- `tasks/cpp-rails-mf-recommender/environment/core/m4t/pack.h`
- `tasks/cpp-rails-mf-recommender/environment/core/p1v/submit.cpp`
- `tasks/cpp-rails-mf-recommender/environment/core/p1v/submit.h`
- `tasks/cpp-rails-mf-recommender/environment/lib/http_util.cpp`
- `tasks/cpp-rails-mf-recommender/environment/lib/http_util.h`
- `tasks/cpp-rails-mf-recommender/environment/decoy/q2n/page.cpp`
- `tasks/cpp-rails-mf-recommender/environment/decoy/n8f/codec.cpp`
- `tasks/cpp-rails-mf-recommender/environment/scripts/build.sh`
- `tasks/cpp-rails-mf-recommender/environment/scripts/start_api.sh`
- `tasks/cpp-rails-mf-recommender/environment/scripts/init_workspace.sh`
- `tasks/cpp-rails-mf-recommender/environment/app/probe_fetch.sh`
- `tasks/cpp-rails-mf-recommender/environment/service/config.ru`
- `tasks/cpp-rails-mf-recommender/environment/service/config/routes.rb`
- `tasks/cpp-rails-mf-recommender/environment/service/app/controllers/ratings_controller.rb`
- `tasks/cpp-rails-mf-recommender/environment/service/app/models/rating_store.rb`
- `tasks/cpp-rails-mf-recommender/environment/service/db/schema.sql`
- `tasks/cpp-rails-mf-recommender/environment/service/db/seeds.sql`
- `tasks/cpp-rails-mf-recommender/environment/data/split_meta.json`
- `tasks/cpp-rails-mf-recommender/environment/docs/bench_precedence.md`
- `tasks/cpp-rails-mf-recommender/environment/docs/api_overview.md`
- `tasks/cpp-rails-mf-recommender/environment/docs/catalog/INDEX.md`
- `tasks/cpp-rails-mf-recommender/environment/docs/catalog/part_01_pagination.md`
- `tasks/cpp-rails-mf-recommender/environment/docs/catalog/part_02_training.md`
- `tasks/cpp-rails-mf-recommender/environment/docs/catalog/part_03_pack_format.md`
- `tasks/cpp-rails-mf-recommender/environment/docs/archive/legacy_pagination.md`
- `tasks/cpp-rails-mf-recommender/environment/config/runtime.toml`
- `tasks/cpp-rails-mf-recommender/environment/platform/verifier-requirements.txt`
- `tasks/cpp-rails-mf-recommender/environment/platform/runtime.json`
- `tasks/cpp-rails-mf-recommender/steps/milestone_1/instruction.md`
- `tasks/cpp-rails-mf-recommender/steps/milestone_1/tests/test.sh`
- `tasks/cpp-rails-mf-recommender/steps/milestone_1/tests/test_m1.py`
- `tasks/cpp-rails-mf-recommender/steps/milestone_1/solution/solve.sh`
- `tasks/cpp-rails-mf-recommender/steps/milestone_1/solution/solve1.sh`
- `tasks/cpp-rails-mf-recommender/steps/milestone_1/solution/patches/m1_pull.patch`
- `tasks/cpp-rails-mf-recommender/steps/milestone_2/instruction.md`
- `tasks/cpp-rails-mf-recommender/steps/milestone_2/tests/test.sh`
- `tasks/cpp-rails-mf-recommender/steps/milestone_2/tests/test_m2.py`
- `tasks/cpp-rails-mf-recommender/steps/milestone_2/solution/solve.sh`
- `tasks/cpp-rails-mf-recommender/steps/milestone_2/solution/solve2.sh`
- `tasks/cpp-rails-mf-recommender/steps/milestone_2/solution/patches/m2_loop.patch`
- `tasks/cpp-rails-mf-recommender/steps/milestone_2/solution/patches/m2_pack.patch`
- `tasks/cpp-rails-mf-recommender/steps/milestone_3/instruction.md`
- `tasks/cpp-rails-mf-recommender/steps/milestone_3/tests/test.sh`
- `tasks/cpp-rails-mf-recommender/steps/milestone_3/tests/test_m3.py`
- `tasks/cpp-rails-mf-recommender/steps/milestone_3/solution/solve.sh`
- `tasks/cpp-rails-mf-recommender/steps/milestone_3/solution/solve3.sh`
- `tasks/cpp-rails-mf-recommender/steps/milestone_3/solution/patches/m3_submit.patch`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/client/k3p/pull.cpp
  symbol: op_fetch
  kind: function
  signature: int op_fetch(const char *base, const char *out_dir)
  purpose: Paginates remote training rows and writes manifest plus jsonl cache.

- path: environment/core/r7n/loop.cpp
  symbol: phase_fit
  kind: function
  signature: int phase_fit(const char *manifest_path, const char *pack_path)
  purpose: Loads cached train rows, runs seeded iterative fit, invokes pack writer.

- path: environment/core/m4t/pack.cpp
  symbol: step_q2
  kind: function
  signature: int step_q2(const char *path, const struct FitState *st)
  purpose: Serializes header, bias vectors, and per-row int8 blocks with scales.

- path: environment/core/p1v/submit.cpp
  symbol: emit_v3
  kind: function
  signature: int emit_v3(const char *base, const char *pack_path, const char *receipt_path)
  purpose: Dequantizes pack, scores holdout pairs, posts batch to remote service.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/client/k3p/pull.cpp
    controls_tests: [test_m1_train_row_count, test_m1_train_sha256, test_m1_pagination_exhaust, test_m1_no_holdout_leak]
  - id: B
    path: environment/core/r7n/loop.cpp
    controls_tests: [test_m2_pack_fingerprint_stable, test_m2_global_mean, test_m2_dequant_dot_sanity, test_m2_bias_nonzero]
  - id: C
    path: environment/core/m4t/pack.cpp
    controls_tests: [test_m2_header_seed, test_m2_train_sha256_match, test_m2_latent_dim]
  - id: D
    path: environment/core/p1v/submit.cpp
    controls_tests: [test_m3_receipt_accepted, test_m3_rmse_threshold, test_m3_n_scored, test_m3_score_range]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/decoy/q2n/page.cpp
  kind: module
  rhymes_with: op_fetch
  non_fix_purpose: Parses static HTML pagination for unrelated audit exports.

- path: environment/decoy/n8f/codec.cpp
  kind: module
  rhymes_with: step_q2
  non_fix_purpose: Base64-encodes diagnostic blobs for log shipping.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [rating, ratings, matrix, factorization, latent, quantize, prediction, predictions, holdout, train, manifest, receipt, rmse, split, pagination, recommender, sgd, ruby, rails, api, sqlite, fetch, submit, service, threshold, artifact, validation, deterministic, compact, inference, endpoint, pairs, users, items, scores, bias, seed, checksum, schema, operator, operators, milestone]
```
