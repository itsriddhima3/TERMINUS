### Decision
GO — Attempt 3. Hard-task calibration locked: long-context bespoke memory-model rules, non-obvious root cause in idiomatic pub-sub, 14-step solver workflow, sixteen tests blocking mutex/atomic/cap-only shortcuts.

### Metadata
- version: 2
- Task name: go-pubsub-happens-before
- Title: Pub-Sub Happens-Before
- Category: debugging
- Languages: ["go", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context"]
- Tags: ["go", "concurrency", "memory-model", "channels", "race-detector"]
- Milestones: 0

## Authoring Brief

### Public contract
Agent receives a Go fan-out distribution service that publishes integer revision snapshots to registered consumers via internal signaling. Running `/app/app/sync_audit.sh` writes `/app/output/sync_audit.json` with `schema_version` 1, fourteen scenario rows, and a `stress_summary` block. Base rows (`burst_delivery`, `graceful_stop`, `late_attach`, `backlog_clear`) report `observed_revision`, `expected_revision`, and `stale_read`. Advanced rows add coupled invariants: `fanout_triple` (three peer labels plus `seq_monotonic`), `mid_detach` (`detached_peer_frozen`, active peer label 91), `branch_toggle` (label 94 after rapid live/stop alternation), `drain_zero_edge` (label 101 with `zero_slot_confused: false`), `relay_sidecar` (`metrics_ok: true` alongside label 88), `coalesce_trace` (label 105 with `coalesce_events: 3`), `registry_grow` (label 112 with `slot_count_delta: 2`), `ack_barrier` (label 116 with `barrier_hits: 4`), `ring_rotate` (label 119 with `slot_index: 2` and `body_digest`), and `package_stress` (`race_exit_code: 0`, `iterations_clean: 500`). Operators report rare stale reads under race-enabled test runs (roughly one per ten thousand iterations) while sequential runs often pass. The HTML reference corpus under `/app/docs/` is the only approved authority for happens-before rules governing signaling teardown. Agent must repair the service so every row reports `stale_read: false` where applicable, all advanced invariants hold, and `go test -race ./...` exits zero.

### Failure topology
Symptoms cluster around teardown and fan-out edges: consumers occasionally observe an earlier revision label after a newer publication completed. Burst and backlog paths mask the defect more often than graceful stop and late attach. The codebase *looks* like idiomatic Go pub-sub — factory helpers, `select` loops, graceful shutdown comments — but embeds a bespoke violation of channel happens-before rules that standard mutex/atomic recipes do not repair under `-race`. The publisher mutates shared payload storage, signals consumers through multiple channel kinds, and closes signaling endpoints during shutdown. Subscribers combine `select` branches for live delivery and stop notification; ordering between payload writes, sends, receives, and closes is inconsistent. Operations notes and inline comments steer toward a wrong root cause (payload locking). The violating edge is stated only in the long HTML memory-model corpus using org-specific terminology ("rendezvous lane" vs "teardown lane"), not in searchable standard Go doc phrasing.

### Environment shape
Dockerized Go module under `/app`: multi-package hub (`p4x` dispatch, `c3s` handoff, `m8t` registry), opaque channel factory (`k7m`), decoy relay/batch helpers, bash audit and scenario drivers, JSON fixture catalogs, and a split HTML memory-model corpus (~65 pages, 15 numbered examples) under `/app/docs/`. Tests invoke the audit harness and race-enabled `go test`.

### Required artifacts
Standard single-step layout: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/` (20+ files), `solution/solve.sh`, `tests/test.sh`, `tests/test_outputs.py`.

### Test plan
- `test_report_schema_version` — `schema_version` equals 1
- `test_all_scenarios_present` — all fourteen scenario keys plus `stress_summary` exist
- `test_burst_delivery_no_stale` — burst row matches expected revision 42, `stale_read` false
- `test_graceful_stop_no_stale` — stop row matches expected revision 57, `stale_read` false
- `test_late_attach_no_stale` — late attach row matches expected revision 63, `stale_read` false
- `test_backlog_clear_no_stale` — backlog row matches expected revision 71, `stale_read` false
- `test_no_scenario_stale_reads` — all rows false on `stale_read`
- `test_race_build_clean` — `go test -race ./...` exit code zero
- `test_seq_monotonic_triple_fanout` — `fanout_triple` peers each match label 88 and `seq_monotonic` is true across the triple
- `test_mid_detach_peer_isolated` — `mid_detach` frozen peer stays at 90 while active peers reach 91 with no stale flag
- `test_nested_branch_toggle_clean` — `branch_toggle` reaches label 94 after rapid alternation without stale reads
- `test_closed_channel_zero_slot_clean` — `drain_zero_edge` label 101 with `zero_slot_confused` false (guards close-zero vs payload confusion)
- `test_metrics_relay_sidecar_intact` — `relay_sidecar` reports `metrics_ok: true` and label 88; decoy relay path must not corrupt handoff
- `test_idle_coalesce_log_intact` — `coalesce_trace` label 105 with exactly three coalesce events per fixture matrix
- `test_registry_grow_under_load` — `registry_grow` label 112 and `slot_count_delta` equals 2 after dynamic slot allocation mid-run
- `test_pending_ack_barrier_clean` — `ack_barrier` label 116 with `barrier_hits` equals 4 (one rendezvous per live peer before teardown)
- `test_ring_slot_visibility_clean` — `ring_rotate` label 119, `slot_index` 2, and `body_digest` matches catalog fixture
- `test_hub_packages_detector_clean` — `package_stress.race_exit_code` is 0 and `iterations_clean` is 500 after hub-scoped `-race` load binary

### Hard task calibration (≤20% model pass target)

Target: **≤20% pass rate** on best or worst frontier models. Task must satisfy **all four** platform hard-task pillars:

| Pillar | How this task satisfies it |
|--------|---------------------------|
| **Deep domain expertise** | Go memory-model channel happens-before (buffered notify teardown vs unbuffered rendezvous) is under-represented in training vs mutex/chan idioms; fix requires mapping org-reframed spec prose to code. |
| **Complex multi-step reasoning (10+)** | Mandatory solver workflow below — **14 sequential steps**; skipping doc reading or fixing one locus fails distinct test subsets. |
| **Subtle debugging / non-obvious root cause** | Symptom is intermittent stale labels; `-race` implicates signaling not payload; ops notes misdirect to locking; idiomatic shutdown pattern is the bug. |
| **Obscure documentation + bespoke rules** | ~65-page HTML corpus reframes standard rules; keyword search for "buffered channel close" must fail; examples 7/11/14 (reviewer-only IDs) encode the edge. |

**Construction-time LLM shortcut traps (must pass in Step 2b):**
- `sync.Mutex` / `sync.RWMutex` around payload → still fails `-race` and `ack_barrier` / `drain_zero_edge`
- `atomic.StoreInt64` on revision label → passes some rows, fails `ring_rotate` body_digest and `-race`
- `cap=0` in factory only → fails `branch_toggle` and `ack_barrier`
- Handoff branch reorder only → fails `graceful_stop` and `package_stress`
- Disabling relay/batch decoys → fails `metrics_relay_sidecar_intact` / `coalesce_trace`

### Mandatory solver workflow (14 steps — Step 2b must enable each)

1. Run `/app/app/sync_audit.sh`; record which of fourteen rows show stale or invariant violations.
2. Run `go test -race ./...`; capture stack traces pointing at hub packages (not payload helpers).
3. Read `/app/docs/operations_notes.md` and **reject** its locking recommendation when `-race` still fires.
4. Open `/app/docs/mem/index.html`; navigate corpus structure (no single searchable "fix me" string).
5. Read channel-synchronization parts (`part_03.html`, `part_05.html`) for rendezvous-lane vs teardown-lane rules.
6. Study worked examples in `/app/docs/mem/examples.html`; identify which example cluster governs close-on-notify-lane behavior.
7. Trace `op_n2` from registry setup in `hub/m8t` through `hub/p4x` — determine notify vs stop lane capacities.
8. Compare live publish path vs teardown path in `phase_r8` — note close order relative to payload write and signal send.
9. Trace `step_w1` `select` branches for failing scenarios (`graceful_stop`, `late_attach`, `drain_zero_edge`).
10. Map doc rule → factory defect (notify lane capacity decouples rendezvous).
11. Map doc rule → dispatch defect (teardown lane closed before rendezvous completes).
12. Map doc rule → handoff defect (stop branch reads slot before draining notify lane to closed).
13. Apply coordinated three-file fix; do **not** add mutex/atomic as primary repair.
14. Re-run full audit + `go test -race ./...` + hub stress (`package_stress`).

### Drafting guardrails
Instruction stays symptoms-only: no channel buffer sizes, no close-before-send recipe, no spec section numbers, no package names on the fix path. Fix-path symbols opaque (`op_n2`, `phase_r8`, `step_w1`). Memory-model HTML uses org-reframed terminology ("rendezvous lane", "teardown lane") — **not** copy-paste phrases from golang.org that enable keyword search. Code symbols must not echo instruction nouns. Decoy modules and operations notes perform genuine work but misdirect naive debuggers. Inline comments in broken dispatch must look vet-approved while encoding wrong teardown order.

### Triviality Ledger

- Adding a mutex around the shared payload passes sequential audit runs but still fails `-race` because the happens-before edge around signaling teardown remains unsynchronized.
- Changing only subscriber `select` ordering fixes late attach in isolation but leaves graceful stop failing when the publisher closes signaling before pending sends rendezvous.
- Setting buffer capacity to zero in the factory alone without reordering publisher close/send and subscriber drain leaves burst scenarios flaky under load simulation.
- Mutex-only patch passes `fanout_triple` sequentially but fails `ack_barrier` because teardown proceeds before per-peer rendezvous completes.
- Reordering handoff branches alone satisfies `branch_toggle` once but fails `drain_zero_edge` when buffered notify still decouples close-zero from payload visibility.
- Patching dispatch without factory alignment passes `mid_detach` for active peers but fails `ring_rotate` when slot rotation races ahead of notify rendezvous.
- Disabling decoy relay metrics to silence noise fails `metrics_relay_sidecar_intact` even if primary rows look clean.
- Following operations_notes mutex guidance clears sequential burst rows but `-race`, `ack_barrier`, and `drain_zero_edge` still fail because happens-before edges around notify lanes remain broken.
- `atomic` stores on revision counters satisfy `fanout_triple` monotonicity cosmetically but fail `ring_rotate` body_digest and hub stress because payload slot bytes lack send/receive synchronization.

### Per-gate Pitfall Inventory

- RC1 — Oracle must touch factory capacity, publisher teardown sequence, and subscriber drain logic; not a one-line race annotation.
- RC6 — Instruction must not cite spec sections, buffer sizes, or fix-path package names.
- RC7 — `solve.sh` includes substantive Go edits across three packages (≥40 LOC non-boilerplate).
- CR1/CR7 — Use committed symbol names `op_n2`, `phase_r8`, `step_w1`; no instruction nouns in fix-path identifiers.
- CR2 — `flipping_point_contract` splits factory, dispatch teardown, and handoff drain across sixteen fix-path tests (max ratio 6/16).
- GX9 — Ground expected revision integers and advanced invariant fields per scenario row in instruction before tests assert them.
- Static checks — `long_context` subcategory requires ≥50k-token semantic doc corpus; reframed terminology must defeat keyword search for standard Go doc headings.
- A24 / ≤20% target — Step 2b verification must confirm mutex-only and cap-only oracle ablations fail ≥6 of 16 flipping tests before claiming hard difficulty.

### Initial Draft Commitments

- `tasks/go-pubsub-happens-before/instruction.md`
- `tasks/go-pubsub-happens-before/task.toml`
- `tasks/go-pubsub-happens-before/output_contract.toml`
- `tasks/go-pubsub-happens-before/environment/Dockerfile`
- `tasks/go-pubsub-happens-before/environment/go.mod`
- `tasks/go-pubsub-happens-before/environment/go.sum`
- `tasks/go-pubsub-happens-before/environment/cmd/daemon/main.go`
- `tasks/go-pubsub-happens-before/environment/pkg/k7m/factory.go`
- `tasks/go-pubsub-happens-before/environment/pkg/k7m/relay.go`
- `tasks/go-pubsub-happens-before/environment/hub/p4x/dispatch.go`
- `tasks/go-pubsub-happens-before/environment/hub/p4x/registry.go`
- `tasks/go-pubsub-happens-before/environment/hub/c3s/handoff.go`
- `tasks/go-pubsub-happens-before/environment/hub/c3s/batch.go`
- `tasks/go-pubsub-happens-before/environment/hub/m8t/types.go`
- `tasks/go-pubsub-happens-before/environment/hub/m8t/payload.go`
- `tasks/go-pubsub-happens-before/environment/internal/trace/trace.go`
- `tasks/go-pubsub-happens-before/environment/app/sync_audit.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_burst.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_stop.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_attach.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_backlog.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_fanout_triple.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_mid_detach.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_branch_toggle.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_drain_zero.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_relay_sidecar.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_coalesce_trace.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_registry_grow.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_ack_barrier.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_ring_rotate.sh`
- `tasks/go-pubsub-happens-before/environment/app/scenario_package_stress.sh`
- `tasks/go-pubsub-happens-before/environment/hub/p4x/stress_test.go`
- `tasks/go-pubsub-happens-before/environment/hub/c3s/handoff_test.go`
- `tasks/go-pubsub-happens-before/environment/lib/run_go.sh`
- `tasks/go-pubsub-happens-before/environment/lib/json_merge.sh`
- `tasks/go-pubsub-happens-before/environment/data/revision_catalog.json`
- `tasks/go-pubsub-happens-before/environment/data/scenario_matrix.json`
- `tasks/go-pubsub-happens-before/environment/docs/mem/part_01.html` through `part_08.html` (part_03 and part_05 encode rendezvous-lane vs teardown-lane rules in org-specific prose)
- `tasks/go-pubsub-happens-before/environment/docs/mem/examples.html`
- `tasks/go-pubsub-happens-before/environment/docs/mem/index.html`
- `tasks/go-pubsub-happens-before/environment/docs/operations_notes.md` (red-herring: recommends payload locking — wrong root cause)
- `tasks/go-pubsub-happens-before/solution/solve.sh`
- `tasks/go-pubsub-happens-before/tests/test.sh`
- `tasks/go-pubsub-happens-before/tests/test_outputs.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/pkg/k7m/factory.go
  symbol: op_n2
  kind: function
  signature: func op_n2(kind int, capHint int) chan struct{}
  purpose: constructs notify and stop signaling channels for hub wiring

- path: environment/hub/p4x/dispatch.go
  symbol: phase_r8
  kind: function
  signature: func phase_r8(ctx context.Context, reg *m8t.Registry, seq int, body []byte) error
  purpose: writes payload slot, signals subscribers, runs graceful stop teardown

- path: environment/hub/c3s/handoff.go
  symbol: step_w1
  kind: function
  signature: func step_w1(ctx context.Context, reg *m8t.Registry, id string) (int, error)
  purpose: subscriber loop receiving signals then reading payload revision
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/pkg/k7m/factory.go
    controls_tests: [test_burst_delivery_no_stale, test_backlog_clear_no_stale, test_seq_monotonic_triple_fanout, test_ring_slot_visibility_clean, test_registry_grow_under_load, test_metrics_relay_sidecar_intact]
  - id: B
    path: environment/hub/p4x/dispatch.go
    controls_tests: [test_graceful_stop_no_stale, test_late_attach_no_stale, test_mid_detach_peer_isolated, test_pending_ack_barrier_clean, test_nested_branch_toggle_clean, test_idle_coalesce_log_intact]
  - id: C
    path: environment/hub/c3s/handoff.go
    controls_tests: [test_no_scenario_stale_reads, test_race_build_clean, test_closed_channel_zero_slot_clean, test_hub_packages_detector_clean]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/pkg/k7m/relay.go
  kind: helper
  rhymes_with: op_n2
  non_fix_purpose: op_q4 multiplexes metrics taps with unrelated buffer sizing for observability only

- path: environment/hub/c3s/batch.go
  kind: helper
  rhymes_with: step_w1
  non_fix_purpose: step_b5 coalesces idle intervals for throughput logging without participating in revision handoff
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [go, fan-out, distribution, service, publishes, revision, snapshots, registered, consumers, internal, signaling, primitives, audit, harness, sync_audit, schema_version, burst, delivery, graceful, stop, late, subscriber, attach, backlog, clearing, scenarios, observed_revision, expected_revision, stale_read, operators, stale, reads, race-enabled, test, suite, iterations, sequential, runs, html, reference, corpus, docs, approved, authority, happens-before, rules, governing, teardown, repair, scenario, race, payload, publication, memory-model, fanout, sync, json, rows, expected, observed, clearing, attach, delivery, stop, graceful, burst]
```
