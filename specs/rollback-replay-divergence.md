### Decision
GO — Attempt 2. Mandated **two independent defect mechanisms** with partial-oracle discrimination, **distributed edits across replay / rollback / reconnect roots**, and a **25+ file** synthetic engine floor so the smallest plausible success is multi-site rather than a single serializer field or RNG constant.

### Metadata
- Task name: rollback-replay-divergence
- Title: Rollback Replay Divergence
- Category: games
- Languages: ["c++"]
- Difficulty: hard
- Codebase size: small
- Subcategories: []
- Tags: ["multiplayer", "determinism", "replay", "rollback", "networking"]
- Milestones: 0

### Anti-trivialization verdict

| Check | Reasoning | Verdict |
| --- | --- | --- |
| Disclosure-collapse | Honest symptoms-only contract still leaves mistaken timelines/defaults unstated; work remains code-directed integration debugging, not translating a fully disclosed policy. | PASS |
| Hidden-instance | Harness uses structured multi-seed matrices, not “pick the one broken artifact.” | PASS |
| Single-artifact repair | At least two mechanistically distinct bugs are required; any single-hunk fix must leave scenarios failing until both are reconciled. | PASS |
| Generalization | Multiple seeds plus disjoint paths (reconnect, rollback bursts, replay export/import, resume) block one-trace memorization. | PASS |
| Prompt-honesty | Symptoms-only honesty does not name the broken mechanism; naming it would violate the public contract. | PASS |
| Cheating-vs-difficulty | Difficulty is cross-layer correctness, not log hiding or tool bans. | PASS |
| Mechanical-fix filter | Risks are conceptual (collapse during build), not verifier plumbing trivia. | PASS |
| Localized-fix | Defects span replay codec, prediction/rollback merge, and reconnect/RNG bootstrap with shared types. | PASS |
| Oracle-locality | Oracle is coordinated surgical edits across modules plus small helpers—no single 40-line file wholesale rewrite. | PASS |
| Small declarative-cluster | Not a one-manifest knob task; core is procedural consistency across sim + replay bytes. | PASS |
| Grep-collapse | Neutral module naming avoids mapping prompt nouns to a uniquely labeled buggy helper. | PASS |
| Pre-factored-helper | No stub helpers named after verifier bullets; names mirror plausible production boundaries. | PASS |
| Recipe-discount | Cookbook rollback snippets only solve isolated pieces; passing requires engine-specific composition. | PASS |
| Security-aura discount | No exploit-story inflation; difficulty is ordinary shipped-game integrity work. | PASS |
| Orthogonal-checklist | Fixes trade replay identity vs resync vs rollback soundness; checklist edits should fail some cell until integrated. | PASS |
| Harness-discount | Seeds add evidence, not answers. | PASS |
| One-pass solvability | Coupling plus falsifiable traces makes single-pass guessing unlikely without running scenarios. | PASS |
| Hard-only gate | Structurally symptoms-only, multi-root, entangled defects—hard-intent; empirical trials validate realization later. | PASS |
| Information delta test | Three non-trivial codebase discoveries are listed under `information_delta` in stored evidence. | PASS |
| Instruction specificity test | Public contract stays symptoms-only (`instruction_specificity.level = symptoms-only`). | PASS |

### Rubric axes
- **Verifiable:** Deterministic hashes and trace slices across seeds give objective scoring. **Pass**
- **Well-specified:** Scenario matrix and artifacts can be pinned in contracts without turning `instruction.md` into an implementation spec. **Pass**
- **Solvable:** Bounded synthetic engine keeps expert investigation finite. **Pass**
- **Difficult:** Entangled mechanisms plus environment breadth target real integration debugging rather than single-hunk trivia. **Pass**
- **Interesting:** Reconnect/replay determinism is paid engineering time in industry multiplayer. **Pass**
- **Outcome-verified:** Grade hashes/traces/replay round-trips, not tools or narration. **Pass**

### Hardness axes
- **Discover:** The agent must run harness scenarios and read scheduling/codec/bootstrap code to learn where timelines diverge; symptoms-only text cannot safely disclose the defective interaction without collapsing diagnosis.
- **Synthesize:** Fixes must reconcile replay bytes, prediction rollback, and reconnect catch-up as one system; no single module owns the end-to-end invariant.
- **Diagnose:** Instruction reports divergence signatures after reconnect/resume while straight-through play matches; causes are inferred, not named.
- **Navigate coupling:** Repairs interfere: tightening replay defaults can break live resync; adjusting snapshot timing can break rollback; tests must force integrated reasoning.
- **Reason beyond training:** Failure modes depend on this engine’s bespoke staging and semantic-default rules, not a drop-in canonical netcode walkthrough.

### Instruction completeness test
No. A symptoms-only `instruction.md` cannot specify mistaken merge order, replay defaulting relative to prediction, or catch-up RNG consumption granularity; the agent must deeply read code and correlate it with harness outputs.

## Authoring Brief

### Public contract
Ship a headless rollback-style multiplayer toy engine under `/app` where straight-through seeded matches are deterministic, but **state hashes and/or canonical trace slices diverge** after **disconnect/reconnect** or **replay resume**, including **replay export → import** round-trips. The agent must restore agreement across the full scenario matrix documented in `output_contract.toml` (absolute artifact paths, hash/trace formats). Do not name broken functions, missing fields, or branch predicates in `instruction.md`.

### Failure topology
Symptoms cluster into three interacting regions: **(A)** timeline semantics around tick/frame advancement and when snapshots capture merged inputs; **(B)** replay serialization that reconstructs late inputs with defaults that disagree with live prediction reconciliation after interruptions; **(C)** reconnect catch-up that replays staged traffic through a path that **consumes RNG draws differently** than steady-state ticks despite matching seed headers. Straight-through runs hide the bug because ordering matches; resume/reconnect paths expose it. Local “fixes” commonly trade replay byte identity against live resync or silently break rollback soundness—tests must catch those regressions.

### Environment shape
Under `environment/` (excluding Docker files), provide a **small** synthetic game engine layout spanning:
- **Gameplay / entity model** (minimal components, deterministic commands).
- **Networking / transport** (framed messages, join/reconnect hooks).
- **Simulation driver** (tick loop, staging of local vs remote inputs, rollback window).
- **Replay subsystem** (record/playback, versioning metadata if needed, export/import).
- **RNG facade** (seeded streams per subsystem boundary).
- **Shared headers/types** used by more than one root so edits propagate.
- **Harness-facing CLI entrypoints** (non-secret) to run scenarios deterministically.
Keep names neutral (production-like). **Minimum 25** non-Docker files to avoid `minimal` blocking.

### Required artifacts
- `instruction.md`, `task.toml`, `output_contract.toml`
- `environment/Dockerfile` (pinned base; `WORKDIR` set; no copying `tests/`, `solution/`, oracle)
- `tests/test.sh` (official non-UI template), `tests/test_outputs.py` (≥6 discoverable tests; `ruff`-clean)
- `solution/solve.sh` (real work; multi-file coordinated fix; deterministic)
- Seeded scenario runner + golden trace/hash contracts as declared

### Test plan
1. **Straight-through determinism:** identical hashes/traces across repeated runs for baseline seeds. (Multi-approach: equivalent state canonicalization allowed.) **Chain: no**
2. **Reconnect matrix:** after forced disconnect/reconnect within bounds, hashes match oracle baseline. **Chain: light harness only** **Chain-dependent: no**
3. **Replay export/import:** recorded blob round-trip reproduces baseline hashes for same commands. **Chain-dependent: no**
4. **Resume-from-mid-replay:** resume path matches fresh-run baseline per contract. **Chain-dependent: no**
5. **Rollback stress:** burst predicted remote corrections still converge post-reconnect. **Chain-dependent: no**
6. **Anti-partial:** disabling/commenting any single intended defect mechanism (as defined during authoring) must fail **≥1** scenario (implemented via internal test hooks or fixture toggles, not instruction leaks). **Chain-dependent: on harness toggles, not agent ordering**
7. **Replay backward compatibility:** older recorded format still loads (if versioning is introduced). **Chain-dependent: no**
8. **RNG stream separation smoke:** subsystem streams remain independent per contract (prevents “fix” by zeroing randomness). **Chain-dependent: no**
9. **Trace schema sanity:** traces parse and include required keys from contract. **Chain-dependent: no**
10. **No wall-clock assertions:** only deterministic proxies. **Chain-dependent: no**

### Drafting guardrails
Avoid `BUG:` markers, “fixme” hotspots, file names that telegraph the defect, test names that reveal patch sites, comments that show correct constants, or metadata/tags that encode the diagnosis. Error strings may be realistic but must not uniquely identify a one-line edit.

## Reviewer Appendix

### Implementation plan
Build a minimal deterministic command-simulation game (no GPU) with a rollback driver, framed network messages, replay recorder/reader, and reconnect simulation hooks. Seed **two independent mistakes** drawn from the failure topology (for example: snapshot boundary vs merge order; replay default input semantics vs prediction reconciliation; catch-up RNG draw cadence vs steady-state ticks). Wire them so **any single-hunk repair fails at least one verifier scenario** under partial-oracle simulation. Provide a deterministic CLI that runs the matrix and writes hashes/traces to absolute paths in `output_contract.toml`. Oracle `solve.sh` applies coordinated patches across modules, updates shared types if needed, and re-runs locally to sanity-check—without embedding test hashes as literals visible to the agent image.

### Proposed file inventory (≥25 non-Docker files)
- `environment/data/seed_scenarios.json` — scripted player command timelines + disconnect markers.
- `environment/include/engine/types.h` — tick ids, player ids, frame/tick typedefs.
- `environment/include/engine/macros.h` — small compile helpers / constants.
- `environment/include/engine/hashable_state.h` — canonical state projection for hashing.
- `environment/include/net/frame.h` — message framing constants.
- `environment/include/replay/header.h` — replay container/version metadata.
- `environment/include/sim/input_stage.h` — staged local/remote input structs.
- `environment/include/sim/rng_facade.h` — subsystem RNG API.
- `environment/src/main.cpp` — CLI entry for harness scenarios.
- `environment/src/game/world.cpp` — entity mutation from commands.
- `environment/src/game/components.cpp` — minimal component storage.
- `environment/src/net/transport.cpp` — encode/decode framed packets.
- `environment/src/net/session.cpp` — join/reconnect state machine.
- `environment/src/net/prediction.cpp` — remote prediction + rollback window ops.
- `environment/src/sim/tick_driver.cpp` — advances ticks, calls staging hooks.
- `environment/src/sim/snapshot.cpp` — snapshot capture/restore.
- `environment/src/sim/input_merge.cpp` — merges predicted vs confirmed inputs.
- `environment/src/sim/command_log.cpp` — canonical command timeline for traces.
- `environment/src/replay/encoder.cpp` — records staged timeline to bytes.
- `environment/src/replay/decoder.cpp` — reconstructs timeline with defaults.
- `environment/src/replay/version.cpp` — format version handling.
- `environment/src/replay/io.cpp` — filesystem read/write helpers.
- `environment/src/replay/resume.cpp` — resume-specific glue (neutral name).
- `environment/src/sim/rng_facade.cpp` — seeded streams + draw accounting.
- `environment/src/harness/runner.cpp` — executes scenario matrix deterministically.
- `environment/src/harness/trace.cpp` — builds trace JSON lines.
- `environment/src/util/checksum.cpp` — stable hashing utilities.
- `environment/src/util/logging.cpp` — deterministic log buffer (optional).
- `environment/src/util/buffer.cpp` — byte buffer helpers for replay I/O.
- `environment/cmake/CMakeLists.txt` — build wiring for the synthetic engine.

### Oracle notes
Oracle builds the project, runs the scenario matrix pre-fix to capture failing signatures, applies **three coordinated edits** (one per root minimum) adjusting: snapshot timing vs merge; replay decoder defaults vs prediction reconciliation expectations; reconnect catch-up tick loop to match steady-state RNG draw cadence. Re-run matrix until all tests pass. Do not copy expected hashes from test sources into the runtime image.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch:
After authoring discipline, the smallest success should span **multiple modules** (shared types + replay + driver/bootstrap). If implementation still permits a one-line fix, **expand coupling** before submission.

Likely editable frontier:
- `environment/src/sim/tick_driver.cpp`, `environment/src/sim/snapshot.cpp`, `environment/src/sim/input_merge.cpp`
- `environment/src/replay/decoder.cpp`, `environment/src/replay/resume.cpp`
- `environment/src/net/session.cpp`, `environment/src/sim/rng_facade.cpp`

Requirement-to-file map:
- Straight-through vs resume divergence → tick driver + snapshot + input merge ordering
- Replay import divergence → replay decoder defaults + resume glue vs prediction timeline
- Post-reconnect RNG fork → session catch-up path + RNG facade cadence

Oracle estimated complexity: ~90–140 lines of non-boilerplate coordinated changes (multi-file), excluding CMake noise.

Red flags:
- none once multi-mechanism rule is enforced during build

Residual hardness:
Integration debugging across timeline semantics, replay bytes, and bootstrap paths with falsifiable trace evidence.

Collapse verdict: PASS

### Per-test feasibility pre-check
- **test_straight_through_determinism:** Checks baseline repeatability. Valid approaches: 2+. Chain-dependent: no. Risk: LOW.
- **test_reconnect_hashes:** Checks reconnect matrix contract. Valid approaches: 2+. Chain-dependent: no. Risk: LOW.
- **test_replay_roundtrip:** Checks export/import identity. Valid approaches: 2+. Chain-dependent: no. Risk: MEDIUM (loosen if alternate canonicalization).
- **test_resume_mid_replay:** Checks resume path. Valid approaches: 2+. Chain-dependent: no. Risk: MEDIUM.
- **test_rollback_burst:** Checks stress path. Valid approaches: 2+. Chain-dependent: no. Risk: MEDIUM.
- **test_partial_defect_disabled:** Ensures verifier discriminates partial fixes. Valid approaches: 1–2 (hook design). Chain-dependent: on internal toggles only. Risk: MEDIUM—ensure toggles are test-only and not shipped as hints.
- **test_replay_old_version_loads:** Versioning compatibility. Valid approaches: 2+. Chain-dependent: no. Risk: LOW.
- **test_rng_streams_independent:** Prevents degenerate fixes. Valid approaches: 2+. Chain-dependent: no. Risk: LOW.
- **test_trace_schema:** Contract parsing. Valid approaches: 2+. Chain-dependent: no. Risk: LOW.
- **test_no_timing_assertions:** Meta-sanity. Valid approaches: 2+. Chain-dependent: no. Risk: LOW.
