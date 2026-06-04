### Decision
GO — Attempt 8. Aligned to CI-CHECKLIST.mdc and REVIEWER-CHECKLIST.mdc.

### Metadata
- Task name: go-meridian-wire-client
- Title: Meridian Wire Client
- Category: software-engineering
- Languages: ["go", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context", "api_integration"]
- Tags: ["go", "openapi", "httptest", "concurrency", "banking"]
- Milestones: 0

## REVIEWER-CHECKLIST.mdc audit (spec stage — Step 2b must confirm on built task)

### Instruction review

PASS

Severity: —

Issue: None at spec stage.

Suggested Fix: Step 2b copies the three-paragraph instruction draft verbatim; run `check_task_absolute_path` after write.

Summary: Concise, human, absolute paths, no hints, no task name, no canary strings.

---

### Environment review

PASS (conditional on Step 2b build)

Severity: —

Issue: Spec commits digest-pinned golang base, tmux+asciinema, .dockerignore, ≤100MB context, narrow COPY, no tests/solution in image.

Suggested Fix: After Dockerfile write, run `check_pinned_images`, `check_sanctioned_base_images`, `check_build_context_size`, `tests_or_solution_in_image`, `check_dockerfile_references`.

Blockers if violated: missing digest pinning (HIGH), privileged/docker.sock (HIGH), hidden solutions in env (HIGH), AI-scaffold filenames (HIGH), env >100MB (HIGH).

---

### Oracle review

PENDING Step 2b

Severity: —

Issue: Oracle not built yet.

Suggested Fix: solve.sh applies wire-fix.patch to op_vault, phase_b3, step_m5; runs compliance_audit.sh; deterministic; offline; no hardcoded scenario JSON.

Critical failures to avoid: randomness, network calls, incomplete implementation.

---

### Verifier review

PASS (conditional on Step 2b build)

Severity: —

Issue: Spec defines canonical offline test.sh + 20 outcome tests.

Suggested Fix: Match reward footer exactly; `UV_OFFLINE=1 uvx` with pinned pytest; ruff clean; no latency tests; oracle and agent use same test.sh.

Critical failures to avoid: partial rewards, missing reward.txt, format-only checks, instruction mismatch.

Verifier checklist mapping:
- reward.txt always assigned — canonical 5-line footer
- oracle and agent tested equally — same test.sh path
- offline — UV_OFFLINE=1, deps baked at Docker build
- binary rewards only — echo 1 or 0
- correctness tested — domain fields in wire_audit.json, not JSON-exists-only
- every instruction requirement tested — compliance_ok + duplicate_postings + harness path

---

### Task structure review (non-milestone)

PASS at spec stage

Required paths committed:
- environment/, environment/Dockerfile
- solution/solve.sh
- tests/test.sh, tests/test_outputs.py
- instruction.md, task.toml, output_contract.toml

---

### Metadata review

PASS at spec stage

- version = "2.0"
- [metadata] complete with anonymous author
- [agent], [verifier], [environment] with allow_internet=false
- tags 3–6; languages match; subcategories include api_integration + long_context
- no docker-compose → no custom_docker_compose flag needed

---

### Rubric review (submission UI — not in task zip)

Step 4: author rubric separately per platform UI.
- minimum 3 negative criteria
- no testing/oracle references in criteria
- valid score values only (no score 4)
- 10–40 cumulative positive points for standard task

---

### CI-CHECKLIST.mdc final validation mapping

| CI final check | Step 2b action |
|----------------|----------------|
| check_pinned_images | Dockerfile every FROM @sha256 |
| check_sanctioned_base_images | golang:1.22-bookworm digest |
| check_build_context_size | du -sh environment/ ≤100MB |
| pinned_dependencies | go.sum + pinned apt + pytest==8.4.1 |
| tests_or_solution_in_image | grep Dockerfile — no COPY tests/solution |
| check_dockerfile_references | no test_outputs.py / solve.sh in Dockerfile |
| check_test_sh | offline uvx template + reward footer |
| check_task_absolute_path | instruction.md paths |
| check_privileged_containers | none |
| validate_task_fields | task.toml complete |
| ruff | test_outputs.py |
| typos | manual pass on instruction + tests |

---

### Hardness (REVIEWER Phase 1 — reasoning required)

Task requires multi-step debugging across compendium + three code packages; twenty scenarios block partial fixes; target ≤20% model pass via engineering depth (not instruction obscurity).

### Discovery budget (construction only — not instruction.md)

- Fingerprint tuple + NFKC normalization → bind + chapter_submission_keys
- First-acceptance TTL anchor → vault + chapter_caller_recovery + precedence memo
- Dual Retry-After formats → backoff + chapter_rate_limits
- Probe/commit shared token → bind + chapter_probe_commit_lifecycle
- Minor-unit-only amount hash → bind + volume_03
- integration_field_notes misdirection → wrong partial fixes

### Naming-pass record

**Instruction nouns extracted:** see authoring spec code_forbidden_tokens

**Test names audited:** 20 tests — no forbidden instruction noun substrings

**Concentration math:** A 7/20, B 6/20, C 7/20; max 0.35; cap 0.5 PASS

### Per-test feasibility

- Tests 1–12: LOW–MEDIUM
- Tests 13–20: HIGH partial-fix blockers
- All deterministic; no latency; outcomes grounded in instruction + compendium

---

## Final decision (spec stage)

**PASS** — spec aligned to CI-CHECKLIST.mdc and REVIEWER-CHECKLIST.mdc.

Summary:
- High failures: 0 (spec stage)
- Medium failures: 0
- Low failures: 0 (oracle/ruff/build pending Step 2b)

**Step 2b must STOP if any CI blocking check fails** (CI-CHECKLIST final decision rule).

Explicit accept/reject for shipped task: **REJECT until Step 2b builds files and oracle 1.0 + NOP 0.0 pass.**
