### Decision
GO — Attempt 8. Aligned to CI-CHECKLIST.mdc (Phases 1–12 + final validation) and REVIEWER-CHECKLIST.mdc (instruction, environment, oracle, verifier, structure, metadata). Offline uv/pytest baked in Dockerfile; canonical test.sh + reward footer; full task.toml + output_contract.toml.

### Metadata
- version: 2
- Task name: go-meridian-wire-client
- Title: Meridian Wire Client
- Category: software-engineering
- Languages: ["go", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context", "api_integration"]
- Tags: ["go", "openapi", "httptest", "concurrency", "banking"]
- Milestones: 0

## Authoring Brief

### Public contract
The Go SDK under `/app` integrates against a local mock wire API. Run `/app/app/compliance_audit.sh` to rebuild `/app/bin/wirectl` and write `/app/output/wire_audit.json`. Normative caller rules live under `/app/docs/meridian_spec/`; `/app/docs/meridian_precedence.md` resolves conflicts with volume 04. `/app/data/scenario_matrix.json` lists twenty scenario keys. Report shape: `schema_version` 1; `scenarios` map with `duplicate_postings`, `completed`, `attempts`, `final_settlement_count`, `outbound_token` (probe/commit rows), `compliance_ok`. Fixture labels grounded in instruction: Acme-Origin, Beta-Dest, Gamma-Vault (`gamma_spaced`, `gamma_compact`, `gamma_alt`), Delta-Port (`delta_cents`, `delta_major_alias`).

### Failure topology
Parallel runs duplicate settlements for one intent while single-threaded runs look fine. Throttled mock responses sometimes never complete. The SDK diverges from the spec compendium in several independent ways — symptoms overlap across token storage, HTTP retry handling, and request dispatch. Misleading `integration_field_notes.md` and decoy config suggest wrong mitigations that pass some rows but not the full matrix.

### instruction.md draft (REVIEWER-CHECKLIST — copy verbatim to instruction.md)

Meridian retail wire integration under `/app` is failing QA on the compliance harness. Run `/app/app/compliance_audit.sh` and inspect `/app/output/wire_audit.json`.

Parallel stress lanes duplicate settlement postings for one logical transfer; single-threaded replays stay clean. Mock gateway throttle responses leave some lanes permanently failed even though the bundled OpenAPI compendium under `/app/docs/meridian_spec/` tells callers how to recover.

Reviewers insist the shipped Go client diverges from that contract in several independent ways. Fix it so every scenario row reports `compliance_ok` true with no duplicate postings.

(REVIEWER-CHECKLIST instruction checks: ≤3 paragraphs; absolute paths; human voice; WHAT not HOW; no task name; no canary strings; no hints/walkthroughs; env docs realistic without hidden STEP lists.)

### output_contract.toml (Step 2b)

```toml
user_visible_outputs = ["/app/output/wire_audit.json"]

internal_harness_files = [
  "/app/app/compliance_audit.sh",
  "/app/data/scenario_matrix.json",
]

[structured_outputs.wire_audit]
target = "/app/output/wire_audit.json"
format = "json"
instruction_checks = [
  "schema_version",
  "scenarios",
  "duplicate_postings",
  "completed",
  "compliance_ok",
  "wire_audit.json",
]
```

### task.toml (Step 2b — REVIEWER metadata checklist)

```toml
version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "software-engineering"
tags = ["go", "openapi", "httptest", "concurrency", "banking"]
languages = ["go", "bash"]
codebase_size = "small"
number_of_milestones = 0
subcategories = ["long_context", "api_integration"]
expert_time_estimate_min = 90
junior_time_estimate_min = 240

[agent]
timeout_sec = 1800

[verifier]
timeout_sec = 900

[environment]
build_timeout_sec = 600
cpus = 2
memory_mb = 4096
storage_mb = 10240
allow_internet = false
```

No docker-compose. Single container only.

### Environment shape
Dockerized Go module at `/app`: golang base with offline uv/pytest baked at build, `wirectl` binary, mock httptest gateway, bash compliance driver, compendium docs (≤8MB tree, pdf shard ≤2MB), decoy helpers. `environment/` total ≤100MB. Verifier reads `/app/output/wire_audit.json` only.

### Required artifacts (REVIEWER task structure — non-milestone)

- `instruction.md`, `task.toml`, `output_contract.toml`
- `environment/Dockerfile`, `environment/.dockerignore`, 24+ env files
- `solution/solve.sh`, `solution/wire-fix.patch`
- `tests/test.sh`, `tests/test_outputs.py`

### Test plan
1. `test_schema_version` — report declares schema_version 1.
2. `test_catalog_scenarios_present` — every key in scenario_matrix appears in output.
3. `test_solo_lane_single_post` — single-threaded Acme-Origin transfer posts once and completes.
4. `test_burst_fan_one_posting` — four concurrent workers on same intent yield duplicate_postings false and final_settlement_count 1.
5. `test_rate_limit_eventually_succeeds` — 429 with delta-seconds Retry-After eventually completes.
6. `test_http_date_retry_after` — 503 with HTTP-date Retry-After eventually completes.
7. `test_reuse_within_window` — second attempt within reuse window reuses token without duplicate posting.
8. `test_expired_key_rotates` — post-expiry attempt mints new token without duplicating prior settlement.
9. `test_cross_intent_isolation` — concurrent distinct beneficiary intents do not cross-post.
10. `test_mixed_amounts_isolated` — same account, different amounts stay distinct.
11. `test_hidden_burst_clean` — hidden burst scenario compliance_ok true.
12. `test_global_audit_clean` — all rows compliance_ok true, zero duplicate_postings.
13. `test_escalating_429_staircase` — increasing delta-seconds Retry-After steps; attempts ≥ 3, completes.
14. `test_probe_commit_shared_token` — probe and commit phases share outbound_token; final_settlement_count 1.
15. `test_anchor_clock_from_acceptance` — delayed retry reuses token when acceptance anchor still valid.
16. `test_beneficiary_normalization_hash` — gamma_spaced/gamma_compact share settlement; gamma_alt isolated.
17. `test_mixed_code_429_then_503` — 429 then 503 with mixed header formats before success.
18. `test_eight_worker_race` — eight concurrent workers, single settlement.
19. `test_minor_unit_fingerprint` — delta_cents and delta_major_alias do not merge.
20. `test_precedence_errata_window` — reuse honors precedence memo over volume 04 errata TTL.

### CI-CHECKLIST.mdc compliance (Step 2b)

| Phase | Requirement | This task |
|-------|-------------|-----------|
| 1 Structural | env/, Dockerfile, tests/test.sh, task.toml, instruction.md | Standard non-milestone layout |
| 2 Instruction | Absolute paths only | `/app/...` in instruction draft |
| 3 Dependencies | Pinned versions, lockfiles | go.sum; pinned apt in Dockerfile; pytest==8.4.1 via uv at build |
| 4 Docker image | Digest pinning, sanctioned base | golang:1.22-bookworm@sha256:… |
| 5 Build context | ≤100MB, ≤50MB/file, .dockerignore | Docs capped; no caches/secrets in env |
| 6 Docker hygiene | Clean apt, no upgrade, no chmod -R, layer order | Single apt RUN; COPY --chmod for scripts |
| 7 Runtime image | No COPY tests/solution; no Dockerfile refs to test_outputs.py or solve.sh | Enforced |
| 8 Verifier | reward.txt always; pytest; binary 0/1; deterministic | Canonical footer below |
| 9 Offline | No runtime pip/curl/apt in test.sh | UV_OFFLINE=1 uvx only |
| 10 Container safety | No privileged, no docker.sock | Single service |
| 11 Metadata | Full task.toml; allow_internet=false | See block above |
| 12 Python | ruff passes on test_outputs.py | Step 2b: `ruff check tasks/.../tests` |

**Final CI validation commands (Step 2b before submit):**
```bash
python3 run_static_checks.py --task-dir tasks/go-meridian-wire-client --version edition_2
ruff check tasks/go-meridian-wire-client/tests/test_outputs.py
./scripts/check-task.sh tasks/go-meridian-wire-client
harbor run -p tasks/go-meridian-wire-client -a oracle
harbor run -p tasks/go-meridian-wire-client -a nop
```

### Dockerfile pattern (CI Phases 4–7 + REVIEWER environment)

- `FROM golang:1.22-bookworm@sha256:<digest>` with OCI labels.
- `WORKDIR /app`; `ENV UV_OFFLINE=1` after baking uv cache at build.
- Build-time only: curl uv tarball (checksum-pinned), `UV_OFFLINE=0 uv tool install pytest==8.4.1 --with pytest-json-ctrf==0.3.5`, warm cache with `uvx pytest --version`.
- Runtime apt (pinned, `--no-install-recommends`, rm lists): **tmux**, **asciinema**, **ca-certificates**, **patch**, **jq** (if needed by audit script).
- Narrow COPY: go.mod first, then cmd/, core/, mock/, decoy/, hub/, app/, lib/, data/, docs/, config/ — never tests/ or solution/.
- `RUN go mod tidy && go build -o /app/bin/wirectl ./cmd/wirectl` — prebuild broken binary in image.
- `CMD ["sleep", "infinity"]`.
- Forbidden in Dockerfile: `COPY tests`, `COPY solution`, references to `test.sh`, `test_outputs.py`, `solve.sh`.

### tests/test.sh (CI Phase 8 — canonical offline template)

```bash
#!/bin/bash

# Offline verifier: Dockerfile warms pytest into /opt/uv-cache; UV_OFFLINE=1 at runtime.
source $HOME/.local/bin/env

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
    exit 1
fi

UV_OFFLINE=1 uvx \
  -p 3.13 \
  -w pytest==8.4.1 \
  -w pytest-json-ctrf==0.3.5 \
  pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
```

No `set -e`. No runtime apt-get/curl. Reward footer must match exactly (REVIEWER verifier checklist).

### Drafting guardrails
Fix-path symbols `op_vault`, `phase_b3`, `step_m5` in code only — never in instruction.md. No AI-scaffold filenames (CLAUDE.md, AGENTS.md, .cursor/). No precomputed `/app/output/wire_audit.json` in environment/. No hidden STEP/HINT in env docs. Verifier rebuilds from agent-edited source inside pytest (compliance_audit.sh) — do not pre-bake golden audit JSON.

### Triviality Ledger

- Mutex-only vault passes solo/burst-4 but fails eight_worker, probe_commit, precedence, gamma, delta rows.
- Integer Retry-After only passes half of throttle rows.
- integration_field_notes sleep/mutex advice fails ≥8 tests.
- volume_04 errata alone fails precedence_errata_window.

### Per-gate Pitfall Inventory

- CI Phase 7 — Dockerfile must not COPY or reference tests/solution/verifier paths.
- CI Phase 9 — test.sh must not curl/apt/pip at runtime; use UV_OFFLINE=1 uvx.
- CI Phase 12 — ruff on test_outputs.py before submit.
- REVIEWER Instruction — no task name, no canary, no walkthrough; ≤3 paragraphs.
- REVIEWER Environment — digest pins, tmux+asciinema, ≤100MB, no AI-scaffold filenames, no hidden solutions in env/.
- REVIEWER Verifier — binary reward only; tests match instruction; no latency assertions.
- REVIEWER Metadata — version 2.0, anonymous author, allow_internet=false, 3–6 tags.

### Initial Draft Commitments

- `tasks/go-meridian-wire-client/task.toml`
- `tasks/go-meridian-wire-client/instruction.md`
- `tasks/go-meridian-wire-client/output_contract.toml`
- `tasks/go-meridian-wire-client/environment/Dockerfile`
- `tasks/go-meridian-wire-client/environment/.dockerignore`
- `tasks/go-meridian-wire-client/environment/go.mod`
- `tasks/go-meridian-wire-client/environment/go.sum`
- `tasks/go-meridian-wire-client/environment/cmd/wirectl/main.go`
- `tasks/go-meridian-wire-client/environment/core/p4k/vault.go`
- `tasks/go-meridian-wire-client/environment/core/t7m/backoff.go`
- `tasks/go-meridian-wire-client/environment/core/t7m/transport.go`
- `tasks/go-meridian-wire-client/environment/core/d2w/bind.go`
- `tasks/go-meridian-wire-client/environment/core/m9q/index.go`
- `tasks/go-meridian-wire-client/environment/mock/gateway/server.go`
- `tasks/go-meridian-wire-client/environment/mock/gateway/handlers.go`
- `tasks/go-meridian-wire-client/environment/decoy/q8n/interval_stub.go`
- `tasks/go-meridian-wire-client/environment/decoy/n3f/keymint.go`
- `tasks/go-meridian-wire-client/environment/decoy/p2x/backoff_table.toml`
- `tasks/go-meridian-wire-client/environment/hub/r1v/spec_scan.go`
- `tasks/go-meridian-wire-client/environment/lib/run_go.sh`
- `tasks/go-meridian-wire-client/environment/app/compliance_audit.sh`
- `tasks/go-meridian-wire-client/environment/app/scenario_a.sh` through `scenario_t.sh`
- `tasks/go-meridian-wire-client/environment/data/scenario_matrix.json`
- `tasks/go-meridian-wire-client/environment/docs/meridian_precedence.md`
- `tasks/go-meridian-wire-client/environment/docs/meridian_spec/index.md`
- `tasks/go-meridian-wire-client/environment/docs/meridian_spec/volume_01_overview.md` through `volume_08_appendix.md`
- `tasks/go-meridian-wire-client/environment/docs/meridian_spec/chapter_submission_keys.md`
- `tasks/go-meridian-wire-client/environment/docs/meridian_spec/chapter_caller_recovery.md`
- `tasks/go-meridian-wire-client/environment/docs/meridian_spec/chapter_rate_limits.md`
- `tasks/go-meridian-wire-client/environment/docs/meridian_spec/chapter_probe_commit_lifecycle.md`
- `tasks/go-meridian-wire-client/environment/docs/meridian_spec/pdf_text_shard.md` (≤2MB)
- `tasks/go-meridian-wire-client/environment/docs/integration_field_notes.md`
- `tasks/go-meridian-wire-client/environment/config/runtime.toml`
- `tasks/go-meridian-wire-client/environment/config/backoff_table.toml`
- `tasks/go-meridian-wire-client/solution/solve.sh`
- `tasks/go-meridian-wire-client/solution/wire-fix.patch`
- `tasks/go-meridian-wire-client/tests/test.sh`
- `tasks/go-meridian-wire-client/tests/test_outputs.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/core/p4k/vault.go
  symbol: op_vault
  kind: function
  signature: func op_vault(slot [32]byte, anchor time.Time) (token string, ok bool)
  purpose: Returns or mints a stable outbound token for a slot with expiry computed from anchor.

- path: environment/core/t7m/backoff.go
  symbol: phase_b3
  kind: function
  signature: func phase_b3(h http.Header, code int) (wait time.Duration, more bool)
  purpose: Derives next wait duration from response metadata for retriable codes.

- path: environment/core/d2w/bind.go
  symbol: step_m5
  kind: function
  signature: func step_m5(a, b, c string, n int64) ([32]byte, error)
  purpose: Hashes caller fields into a stable slot identity for downstream token lookup.
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/core/p4k/vault.go
    controls_tests: [test_burst_fan_one_posting, test_reuse_within_window, test_expired_key_rotates, test_hidden_burst_clean, test_anchor_clock_from_acceptance, test_eight_worker_race, test_precedence_errata_window]
  - id: B
    path: environment/core/t7m/backoff.go
    controls_tests: [test_rate_limit_eventually_succeeds, test_http_date_retry_after, test_solo_lane_single_post, test_global_audit_clean, test_escalating_429_staircase, test_mixed_code_429_then_503]
  - id: C
    path: environment/core/d2w/bind.go
    controls_tests: [test_cross_intent_isolation, test_mixed_amounts_isolated, test_catalog_scenarios_present, test_schema_version, test_probe_commit_shared_token, test_beneficiary_normalization_hash, test_minor_unit_fingerprint]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/decoy/q8n/interval_stub.go
  kind: module
  rhymes_with: phase_b3
  non_fix_purpose: Fixed-interval helper used by deprecated CLI flag only.

- path: environment/decoy/n3f/keymint.go
  kind: helper
  rhymes_with: op_vault
  non_fix_purpose: UUID-per-request mint for load-test tooling, not on settlement hot path.

- path: environment/decoy/p2x/backoff_table.toml
  kind: config-reader
  rhymes_with: phase_b3
  non_fix_purpose: Stale retry intervals from deprecated annex; not on hot path.

- path: environment/hub/r1v/spec_scan.go
  kind: module
  rhymes_with: step_m5
  non_fix_purpose: Indexes OpenAPI headings for lint script without binding fingerprints.
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [Meridian, retail, wire, integration, app, QA, compliance, harness, compliance_audit, output, wire_audit, json, Parallel, stress, lanes, duplicate, settlement, postings, logical, transfer, single-threaded, replays, Mock, gateway, throttle, responses, permanently, failed, bundled, OpenAPI, compendium, meridian_spec, callers, recover, Reviewers, shipped, Go, client, diverges, contract, ways]
```
