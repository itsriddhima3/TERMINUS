### Decision
GO — Attempt 3. Hard-task calibration documented: ≤20% target, 14-step workflow, org-reframed long-context docs, mutex/atomic/cap-only shortcut traps.

### Metadata
- Task name: go-pubsub-happens-before
- Title: Pub-Sub Happens-Before
- Category: debugging
- Languages: ["go", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context"]
- Tags: ["go", "concurrency", "memory-model", "channels", "race-detector"]
- Milestones: 0

### Discovery budget
- Discovery: notify channels are allocated with nonzero capacity while payload slots mutate before rendezvous completes, so close/teardown can precede unconsumed signals.
  Planned location: `environment/pkg/k7m/factory.go` (`op_n2`)
  Why instruction must not reveal it: naming buffer capacity collapses diagnosis to "set cap=0" without reading the memory-model examples on close vs send ordering.

- Discovery: graceful stop closes the notify endpoint before final payload send rendezvous and before subscribers drain pending signals.
  Planned location: `environment/hub/p4x/dispatch.go` (`phase_r8`)
  Why instruction must not reveal it: stating "close before send" is the entire fix recipe.

- Discovery: subscribers read payload revision on the stop branch before draining notify until closed, relying on close-zero receive without a prior matching send edge.
  Planned location: `environment/hub/c3s/handoff.go` (`step_w1`)
  Why instruction must not reveal it: naming the branch order turns the task into a one-line reorder patch.

- Discovery: the violating edge is documented in the memory-model corpus example cluster contrasting buffered notify teardown with unbuffered rendezvous (spec Section 5.3 analog); agents must map prose to code paths.
  Planned location: `environment/docs/mem/examples.html` (examples 7, 11, 14)
  Why instruction must not reveal it: citing section numbers or example IDs enables keyword search without semantic reading.

- Discovery: `/app/docs/operations_notes.md` recommends payload mutex locking — a plausible but wrong fix that passes some sequential scenarios.
  Planned location: `environment/docs/operations_notes.md`
  Why instruction must not reveal it: naming the red herring collapses debugging to "ignore ops notes."

- Discovery: org-specific doc terms "rendezvous lane" / "teardown lane" in part_05 replace searchable standard Go phrasing; agents must read semantically.
  Planned location: `environment/docs/mem/part_05.html`
  Why instruction must not reveal it: mapping terms to standard MM vocabulary is core difficulty.

### Anti-trivialization verdict

| # | Check | Verdict | Reasoning |
|---|-------|---------|-----------|
| 1 | Disclosure-collapse | PASS | Honest symptoms-only instruction does not state buffer size, close order, or spec section |
| 2 | Hidden-instance | PASS | No single broken file; defect is cross-package ordering |
| 3 | Single-artifact repair | PASS | Factory-only or handoff-only patches fail subset of scenarios and `-race` |
| 4 | Generalization | PASS | Four scenarios plus race build cover multiple teardown/orderings |
| 5 | Prompt-honesty | PASS | Naming the bug class still requires mapping corpus → three code loci |
| 6 | Cheating-vs-difficulty | PASS | Anti-cheat is audit JSON + race build, not the hardness source |
| 7 | Mechanical-fix filter | PASS | Core work is synchronization logic, not harness tuning |
| 8 | Localized-fix | PASS | No one function passes all tests |
| 9 | Oracle-locality | PASS | Oracle edits three packages with coordinated semantics |
| 10 | Small declarative-cluster | PASS | Not a config-knob task |
| 11 | Grep-collapse | PASS | Instruction nouns banned from fix-path symbols; docs use standard terms only in HTML |
| 12 | Pre-factored-helper | PASS | Opaque names (`op_n2`, `phase_r8`, `step_w1`) |
| 13 | Recipe-discount | PASS | Not a textbook mutex/sprinkle recipe; requires memory-model reasoning |
| 14 | Security-aura discount | PASS | Concurrency correctness, not CVE trivia |
| 15 | Orthogonal-checklist | PASS | Scenarios share coupled happens-before failure mode |
| 16 | Harness-discount | PASS | Docker/bash harness is realism, not difficulty |
| 17 | One-pass solvability | PASS | Requires doc reading + multi-file coordination |
| 18 | Hard-only gate | PASS | Clearly hard when instruction omits cause |
| 19 | Discovery budget | PASS | Four discoveries listed above |
| 20 | Instruction specificity | PASS | Symptoms-only level |
| 21 | Topology distribution | PASS | Three topologies enumerated below |

### Topology enumeration (3 candidate fix topologies)
1. **Handoff-only drain reorder** — `step_w1` drains notify before reading payload on stop; fails burst/backlog when factory buffer allows signals ahead of payload visibility. Requires `handoff.go` + `factory.go`.
2. **Dispatch-only send-before-close** — `phase_r8` sends sentinel before close; fails late attach when factory buffer decouples send from receive and handoff still reads early. Requires `dispatch.go` + `handoff.go` + `factory.go`.
3. **Full rendezvous alignment** — unbuffered notify (or drain-until-closed), send-before-close teardown, subscriber drain-then-read; only topology passing all scenarios and `-race`. Requires all three loci.

### Rubric axes
- **Verifiable** — PASS: deterministic JSON audit + `go test -race` exit code.
- **Well-specified** — PASS: fourteen scenario rows plus stress_summary with typed invariant fields.
- **Solvable** — PASS: expert Go engineer + memory model in hours.
- **Difficult** — PASS: subtle channel close/send happens-before coupling across files.
- **Interesting** — PASS: real pub-sub stale-read incidents in production Go services.
- **Outcome-verified** — PASS: grades audit JSON and race build, not reading notes.

### Hard task calibration (≤20% model pass target)

**Empirical target:** ≤20% on best or worst frontier model after Step 4 benchmark.

| User criterion | Pass? | Evidence |
|----------------|-------|----------|
| Deep domain expertise | YES | Go memory-model channel HB edges (not common mutex patterns); org-reframed 65-page corpus |
| 10+ sequential steps | YES | 14-step mandatory workflow in authoring spec |
| Subtle debugging / non-obvious root cause | YES | Intermittent stale labels; ops-notes misdirection; idiomatic shutdown is the bug |
| Obscure documentation | YES | long_context ≥50k tokens; reframed terminology defeats keyword search |
| Bespoke rules in common patterns | YES | Looks like standard pub-sub + graceful shutdown; violates custom rendezvous-lane rule |
| Niche tools | PARTIAL | Go + `-race` are common; hardness comes from MM + long context, not language rarity |

**Predicted model failure modes (design intent):**
1. Add mutex from operations_notes → partial pass, `-race` fail (~40% of naive attempts)
2. Set cap=0 without dispatch/handoff → subset pass (~25%)
3. Reorder select only → branch_toggle pass, stop/ack fail (~30%)
4. Never read docs/mem → grep relay/batch decoys (~20%)
5. Full correct fix → ≤20% ceiling target

### Hardness axes
- **Discover** — Agents must read HTML corpus (reframed terms), reject ops-notes mutex advice, and correlate `-race` stacks with notify lanes.
- **Synthesize** — Factory capacity, publisher teardown, and subscriber handoff interact; decoy relay/batch must remain intact.
- **Diagnose** — Instruction gives stale-read rate symptom; root cause is non-obvious signaling ordering, not payload corruption.
- **Navigate coupling** — Mutex, atomic, cap-only, and handoff-only patches each fail distinct advanced tests.
- **Reason beyond training** — Requires deriving fix from org-specific memory-model prose about rendezvous vs teardown lanes — not pattern-matching "always use mutex with shared state" or "buffered channels for perf."

### Instruction completeness test
Cannot solve from instruction alone. Agent must run `sync_audit.sh`, inspect `-race` output, read `/app/docs/mem/` corpus, and trace cross-package signaling flow.

## Reviewer Appendix

### Implementation plan
Single-container Go 1.22 image with multi-package hub simulating revision fan-out. Broken code uses buffered notify channels, closes notify during graceful stop before send rendezvous, and lets subscribers read payload on stop branch without draining. Memory-model HTML corpus (~65 pages split across parts + 15 examples) embeds channel happens-before teaching material including buffered-close vs unbuffered rendezvous contrasts without pointing to code symbols. Audit bash driver runs fourteen scenario scripts plus hub `-race` stress binary producing merged JSON with `stress_summary`. Oracle adjusts `op_n2` capacity/wiring, reorders `phase_r8` send/close, and rewrites `step_w1` drain-then-read loop.

### Proposed file inventory
38 files under `environment/`: `cmd/`, `pkg/k7m/`, `hub/p4x/`, `hub/c3s/`, `hub/m8t/`, `internal/trace/`, `app/` (14 scenario scripts), `lib/`, `data/`, `docs/mem/` (9 HTML parts), `docs/operations_notes.md`, module files, Dockerfile.

### Oracle notes
`solve.sh` patches `factory.go` (unbuffered notify or cap=0 for rendezvous path), `dispatch.go` (final send before close; wait for subscriber ack where needed), `handoff.go` (drain notify until closed before reading payload on stop path). Rebuilds module and runs audit + race tests.

### Collapse audit
Stage: implementation-plan

Smallest plausible successful patch: unbuffered notify + send-before-close + drain-then-read — but agent must discover all three from corpus and failing stop/attach scenarios.

Likely editable frontier: `pkg/k7m/factory.go`, `hub/p4x/dispatch.go`, `hub/c3s/handoff.go`

Requirement-to-file map:
- stale on graceful stop → dispatch close order + handoff stop branch
- stale on late attach → factory buffer + handoff live branch
- `-race` failures → all three coordinated

Oracle estimated complexity: ~55 lines non-boilerplate Go across three files

Red flags:
- Intermittent 1/10k symptom must not be sole verifier; `-race` and stop/attach scenarios provide deterministic signal

Residual hardness:
After opening code, agent must semantically read ~65 pages of org-reframed memory-model HTML, reject operations_notes mutex guidance, and coordinate three opaque loci — mutex/atomic/cap-only shortcuts fail ≥6 flipping tests and `-race`. Expected frontier model pass rate ≤20%.

Collapse verdict: PASS (calibrated for hard-only / ≤20% target)

### Naming-pass record

**Instruction nouns extracted:**
go, fan-out, distribution, service, publishes, revision, snapshots, registered, consumers, internal, signaling, primitives, audit, harness, sync_audit, schema_version, burst, delivery, graceful, stop, late, subscriber, attach, backlog, clearing, scenarios, observed_revision, expected_revision, stale_read, operators, stale, reads, race-enabled, test, suite, iterations, sequential, runs, html, reference, corpus, docs, approved, authority, happens-before, rules, governing, teardown, repair, scenario, race, payload, publication, memory-model, fanout, sync, json, rows, expected, observed, clearing, attach, delivery, stop, graceful, burst

**Renames during drafting:**
- `publish.go` → `dispatch.go`: avoid "publish" noun collision with instruction
- `consume.go` → `handoff.go`: avoid "consumer/subscriber" echo in path
- `channel_factory` → `op_n2`: opaque symbol per manifest

**Test names audited:**
- test_report_schema_version
- test_all_scenarios_present
- test_burst_delivery_no_stale
- test_graceful_stop_no_stale
- test_late_attach_no_stale
- test_backlog_clear_no_stale
- test_no_scenario_stale_reads
- test_race_build_clean
- test_seq_monotonic_triple_fanout
- test_mid_detach_peer_isolated
- test_nested_branch_toggle_clean
- test_closed_channel_zero_slot_clean
- test_metrics_relay_sidecar_intact
- test_idle_coalesce_log_intact
- test_registry_grow_under_load
- test_pending_ack_barrier_clean
- test_ring_slot_visibility_clean
- test_hub_packages_detector_clean

**Concentration math:**
- Total tests across flipping_point_contract: 16
- A (`pkg/k7m/factory.go`): 6/16 = 0.375
- B (`hub/p4x/dispatch.go`): 6/16 = 0.375
- C (`hub/c3s/handoff.go`): 4/16 = 0.25
- Cap: 0.5. Max ratio observed: 0.375. Status: PASS

### Per-test feasibility pre-check
- test_report_schema_version — schema guard; LOW; chain-dependent no
- test_all_scenarios_present — fourteen keys + stress_summary; LOW; no
- test_burst_delivery_no_stale — revision 42; LOW; yes on factory+dispatch
- test_graceful_stop_no_stale — revision 57; MEDIUM; yes on dispatch+handoff
- test_late_attach_no_stale — revision 63; MEDIUM; yes on factory+handoff
- test_backlog_clear_no_stale — revision 71; LOW; yes on factory+dispatch
- test_no_scenario_stale_reads — aggregate; LOW; all three loci
- test_race_build_clean — `-race` whole module; LOW; requires coordinated fix
- test_seq_monotonic_triple_fanout — triple peer monotonic seq; HIGH; factory rendezvous + dispatch fan-out ordering; chain-dependent yes
- test_mid_detach_peer_isolated — frozen vs active peer labels; HIGH; dispatch detach timing + handoff branch; yes
- test_nested_branch_toggle_clean — rapid alternation label 94; HIGH; handoff select + dispatch signal interleave; yes
- test_closed_channel_zero_slot_clean — zero_slot_confused guard; HIGH; handoff drain-then-read + factory cap; yes
- test_metrics_relay_sidecar_intact — decoy non-interference; MEDIUM; factory buffer must not break relay sidecar; 2+ approaches if relay isolated by design
- test_idle_coalesce_log_intact — coalesce_events==3; MEDIUM; dispatch windowing + batch decoy; chain-dependent yes
- test_registry_grow_under_load — slot_count_delta==2; HIGH; registry mutation under notify in flight; factory+dispatch
- test_pending_ack_barrier_clean — barrier_hits==4; HIGH; dispatch must rendezvous all peers before teardown; yes
- test_ring_slot_visibility_clean — slot_index + body_digest; HIGH; payload ring rotation vs notify ordering; factory+handoff
- test_hub_packages_detector_clean — 500-iteration hub `-race` stress; HIGH; all three loci; 1 valid approach
