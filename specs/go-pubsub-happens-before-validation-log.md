# go-pubsub-happens-before validation log

## Attempt 4 — Step 2b alignment (DOCKER / INSTRUCTION / TASK-QUALITY)

**Decision:** Step 2b task built and aligned to DOCKER-ENV, DOCKER-IMG, INSTRUCTION, and TASK-QUALITY rules.

**Alignment changes:**
- **Docker:** Single-stage `golang:1.22-bookworm@sha256:…` with digest pinning; pinned apt packages; `tmux` + `asciinema`; narrow COPY; `.dockerignore`; offline uv cache warmup (`UV_CACHE_DIR`, no runtime pytest pip); `CGO_ENABLED=1` + `gcc` for `-race`; `allow_internet=false`.
- **Instruction:** Three paragraphs, symptoms-only, absolute paths, schema field names without numeric answer key; expected values delegated to `/app/data/scenario_matrix.json`.
- **Verifier:** Official `tests/test.sh` uvx prefix; 18 deterministic pytest tests with docstrings; binary reward via `/logs/verifier/reward.txt`.
- **NOP fix:** Broken teardown uses `close` → `Gosched` → `Write` with handoff read-before-drain; `TestHandoffStopPath` fails under `-race`; scenar reports `stale_read=true` on `graceful_stop` and `drain_zero_edge`.
- **Oracle:** Targeted Python edits in `solve.sh` (unbuffered notify, write-before-close, drain-then-read); rebuilds scenar and re-runs audit.

**Gate evidence (local Docker):**
- `python3 run_static_checks.py --task-dir tasks/go-pubsub-happens-before --version edition_2` → **PASS** (1 WARN: uv in Dockerfile — matches plc-line-sync-recovery).
- NOP (no solve.sh): reward **0** (5/18 tests fail).
- Oracle (solve.sh + test.sh): reward **1** (18/18 pass).
- `collapse_check.py`: 6 FAIL / 4 WARN / 13 PASS (GX2/GX8 fixed; RC4 tamper surface, GX9 saturation, GX3 edit distance remain).

**Next step:** Harbor oracle 1× + NOP; oracle 10× before submission.

---

## Attempt 3 — GO (hard-task calibration)

**Decision:** GO — Attempt 3. Locked ≤20% model pass target with 14-step workflow, org-reframed long-context docs, operations_notes red herring, and explicit mutex/atomic/cap-only shortcut traps.

**Changes:**
- Added `### Hard task calibration (≤20% model pass target)` with four-pillar mapping.
- Added 14-step mandatory solver workflow.
- Added LLM shortcut trap matrix (mutex, atomic, cap-only, handoff-only, decoy disable).
- Reframed memory-model corpus to use org-specific "rendezvous lane" / "teardown lane" terminology.
- Added operations_notes red herring and two triviality-ledger bullets for atomic/mutex paths.
- Expanded discovery budget to 6 items in reviewer appendix.
- Updated collapse audit for ≤20% empirical target.

**Step 2b gates:** Oracle ablation must confirm mutex-only and cap-only patches fail ≥6/16 flipping tests before submission.

---

## Attempt 2 — GO (expanded test plan)

**Decision:** GO — Attempt 2. Added ten advanced scenario invariants and hub-scoped stress tests; eighteen total verifier tests (sixteen in flipping contract).

**Changes:**
- Expanded `sync_audit.json` contract to fourteen scenario rows plus `stress_summary`.
- Added ten opaque-named hard tests exercising triple fan-out monotonicity, mid-detach isolation, branch toggle, close-zero edge, relay decoy non-interference, coalesce trace, registry growth, ack barrier, ring slot visibility, and hub package `-race` stress.
- Redistributed flipping_point_contract: A 6/16, B 6/16, C 4/16 (max 0.375).
- Added ten scenario shell scripts and hub stress test files to Initial Draft Commitments.

**Next step:** Step 2b — draft task files including advanced scenario drivers.

---

## Attempt 1 — GO

**Decision:** GO — Attempt 1. Go pub-sub happens-before with long-context memory-model corpus and distributed fix across k7m/p4x/c3s.

**Changes from raw pitch:**
- Category mapped to `debugging` (not "Long Context"; that is subcategory `long_context`).
- Removed Section 5.3 / unbuffered-vs-buffered close hint from public instruction (symptoms-only).
- Replaced probabilistic 1/10k-only verification with deterministic `-race` build + scenario audit JSON.
- Assigned opaque fix-path symbols and flipping_point_contract across three packages.

**Artifacts:**
- `specs/go-pubsub-happens-before.md` (authoring spec)
- `specs/go-pubsub-happens-before-reviewer.md` (reviewer appendix)
- `specs/go-pubsub-happens-before-attempt-1-evidence.json`
- `specs/go-pubsub-happens-before-rubrics.txt`

**Next step:** Step 2b — draft task files from authoring spec Initial Draft Commitments.
