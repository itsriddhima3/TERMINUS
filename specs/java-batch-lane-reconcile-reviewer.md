### Decision
GO — Attempt 1 (calibration pass). Aligned to CI-CHECKLIST.mdc and REVIEWER-CHECKLIST.mdc.

### Metadata
- Task name: java-batch-lane-reconcile
- Title: Batch Lane Reconcile
- Category: debugging
- Languages: ["java", "sql", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["db_interaction", "tool_specific", "long_context"]
- Tags: ["java", "spring", "postgresql", "jpa", "concurrency", "bash"]
- Milestones: 0

## REVIEWER-CHECKLIST.mdc audit (spec stage — Step 2b must confirm on built task)

### Instruction review

PASS

Severity: —

Issue: None at spec stage.

Suggested Fix: Step 2b copies the three-paragraph instruction draft verbatim; run `check_task_absolute_path` after write.

Summary: Concise, human, absolute paths, grounded partition caps (6/10/4) and lane_audit.json outcome fields; no hints, no task name, no canary strings; no walkthroughs.

---

### Environment review

PASS (conditional on Step 2b build)

Severity: —

Issue: Spec commits digest-pinned base, tmux+asciinema, .dockerignore, ≤100MB context, narrow COPY, no tests/solution in image, multi-stage Maven build.

Suggested Fix: After Dockerfile write, run `check_pinned_images`, `check_sanctioned_base_images`, `check_build_context_size`, `tests_or_solution_in_image`, `check_dockerfile_references`.

Blockers if violated: missing digest pinning (HIGH), privileged/docker.sock (HIGH), hidden solutions in env (HIGH), AI-scaffold filenames (HIGH), env >100MB (HIGH), runtime internet (HIGH).

---

### Oracle review

PENDING Step 2b

Severity: —

Issue: Oracle not built yet.

Suggested Fix: solve.sh applies coordinated fixes to cfg_p9, op_n2, step_w1, phase_r8; runs lane_audit.sh; deterministic; offline; no hardcoded lane_audit.json.

Critical failures to avoid: randomness, network calls, incomplete implementation, hardcoded audit JSON.

---

### Verifier review

PASS (conditional on Step 2b build)

Severity: —

Issue: Spec defines canonical offline test.sh + 23 outcome tests.

Suggested Fix: Match reward footer exactly; `UV_OFFLINE=1 uvx` with pinned pytest; ruff clean; no latency tests; oracle and agent use same test.sh.

Critical failures to avoid: partial rewards, missing reward.txt, format-only checks, instruction mismatch.

Verifier checklist mapping:
- reward.txt always assigned — canonical 5-line footer
- oracle and agent tested equally — same test.sh path
- offline — UV_OFFLINE=1, deps baked at Docker build
- binary rewards only — echo 1 or 0
- correctness tested — lost_rows, duplicate_external_keys, unstable_totals, ingest_compliance, DB cross-checks
- every instruction requirement tested — caps, stress_summary, scenario matrix

---

### Task structure review (non-milestone)

PASS at spec stage

Required paths committed:
- environment/, environment/Dockerfile
- solution/solve.sh
- tests/test.sh, tests/test_outputs.py
- instruction.md, task.toml, output_contract.toml

Reject if: root-level milestone layout, missing solution/ or tests/.

---

### Metadata review

PASS at spec stage

- version = "2.0"
- [metadata] complete with anonymous author
- [agent], [verifier], [environment] with allow_internet=false
- verifier.timeout_sec (900) ≥ build_timeout_sec (900)
- tags 3–6; languages match; subcategories include db_interaction + tool_specific + long_context
- no docker-compose → no custom_docker_compose flag needed
- number_of_milestones = 0

---

### Rubric review (submission UI — not in task zip)

PASS at spec stage — see specs/java-batch-lane-reconcile-rubrics.txt

- 7 negative criteria (≥3 required)
- 10 positive criteria; cumulative +39 within 10–40 range for standard task
- no score 4 values
- no pytest/test function names in criteria
- no oracle/solve.sh references
- positive phrasing on reward lines

---

### CI-CHECKLIST.mdc final validation mapping

| CI final check | Step 2b action |
|----------------|----------------|
| check_pinned_images | Dockerfile every FROM @sha256 |
| check_sanctioned_base_images | debian or postgres bookworm digest |
| check_build_context_size | du -sh environment/ ≤100MB |
| pinned_dependencies | pom.xml + pinned apt + pytest==8.4.1 |
| tests_or_solution_in_image | grep Dockerfile — no COPY tests/solution |
| check_dockerfile_references | no test_outputs.py / solve.sh in Dockerfile |
| check_test_sh | offline uvx template + reward footer |
| check_task_absolute_path | instruction.md paths |
| check_privileged_containers | none |
| validate_task_fields | task.toml complete |
| ruff | test_outputs.py |
| typos | manual pass on instruction + tests |

---

### Discovery budget (construction only — not instruction.md)

- YAML vs Hikari connectionInitSql observation-frame downgrade → cfg_p9 + boundary_contract part_02/03
- Header-before-line flush vs child-first rollup trigger → op_n2 + step_w1 + part_04
- Stamp on header while lines mutate → entities + op_n2
- phase_r8 retries inside commit frame → phase_r8 + examples 8/11
- operations_notes / PessimisticAdvice misdirection

### Hardness axes (REVIEWER — reasoning required)

Task requires multi-step debugging across boundary corpus + four code/SQL loci; 23 tests block partial fixes; target ≤20% model pass via engineering depth.

### Naming-pass record

**Instruction nouns extracted:** spring, boot, chunk, ingest, service, loses, rows, duplicates, business, keys, whenever, parallel, uploads, single-threaded, replays, north-shelf, east-crate, west-bin, lane_audit, read, report, judge, playbooks, database, tuning, qa, thinks, breaking, several, invariants, boundary, material, disagrees, playbook, follow, bench_precedence, conflict, need, every, scenario, lost, duplicate, external, stable, rollup, totals, ingest_compliance, fine, still, look, stress_summary, block, should, end, those, families

**Test names audited:** 23 tests — no forbidden instruction noun substrings

**Concentration math:** A 11/23, B 7/23, C 6/23, D 5/23; max 0.478; cap 0.5 PASS

### Per-test feasibility

- Tests 1–13: LOW–MEDIUM
- Tests 14–23: HIGH partial-fix blockers
- All deterministic; no latency; outcomes grounded in instruction + lane_audit.json

---

## Final decision (spec stage)

**PASS** — spec aligned to CI-CHECKLIST.mdc and REVIEWER-CHECKLIST.mdc.

Summary:
- High failures: 0 (spec stage)
- Medium failures: 0
- Low failures: 0 (oracle/ruff/build pending Step 2b)

**Step 2b must STOP if any CI blocking check fails** (CI-CHECKLIST final decision rule).

Explicit accept/reject for shipped task: **REJECT until Step 2b builds `tasks/java-batch-lane-reconcile/` and oracle 1× + NOP 0.0 pass.**
