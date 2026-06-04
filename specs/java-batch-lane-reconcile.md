### Decision
GO — Attempt 1 (calibration pass). Aligned to CI-CHECKLIST.mdc (Phases 1–12 + final validation) and REVIEWER-CHECKLIST.mdc (instruction, environment, oracle, verifier, structure, metadata, rubric). Offline uv/pytest baked in Dockerfile; canonical test.sh + reward footer; full task.toml + output_contract.toml.

### Metadata
- version: 2
- Task name: java-batch-lane-reconcile
- Title: Batch Lane Reconcile
- Category: debugging
- Languages: ["java", "sql", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["db_interaction", "tool_specific", "long_context"]
- Tags: ["java", "spring", "postgresql", "jpa", "concurrency", "bash", "transactions"]
- Milestones: 0

## Authoring Brief

### Public contract
The Spring Boot facility under `/app` ingests large chunked uploads for three shelf families — North-Shelf (six active slots), East-Crate (ten), West-Bin (four). `/app/app/lane_audit.sh` writes `/app/output/lane_audit.json` with `schema_version` 1, `catalog_partitions`, a `scenarios` map, and `ingest_compliance` flags. Each scenario row reports `lost_rows`, `duplicate_external_keys`, `unstable_totals`, `chunks_attempted`, and (for advanced rows) `line_parity_ok`, `rollup_monotone`, `read_after_write_ok`. Parallel stress lanes drop accepted records and collide on business keys while single-threaded replays stay clean; mixed-family bursts cross-taint rollup totals. Twenty-two scenario keys in the matrix exercise solo through triple-fanout bursts. Agent must repair the facility so every scenario shows zero drops, zero key collisions, stable rollup totals, and `ingest_compliance` true. Grading reads `/app/output/lane_audit.json`.

### instruction.md draft (REVIEWER-CHECKLIST — copy verbatim to instruction.md)

Our Spring Boot chunk ingest service at `/app` loses rows and duplicates business keys when we run parallel uploads on North-Shelf (six active slots), East-Crate (ten), or West-Bin (four). Single-threaded replays on those families still look fine.

Run `/app/app/lane_audit.sh` and read `/app/output/lane_audit.json` — that report is how we will judge the fix. Each scenario row should end with `lost_rows` 0, `duplicate_external_keys` 0, `unstable_totals` false, and `ingest_compliance` true. The `stress_summary` block should report zero loss events when the full matrix is clean.

The playbooks under `/app/docs/` blame database tuning, but QA thinks we are breaking several invariants at once. If the boundary material under `/app/docs/boundary_contract/` disagrees with a playbook, follow the boundary spec; `/app/docs/bench_precedence.md` says how to resolve that conflict.

(REVIEWER-CHECKLIST instruction checks: ≤3 paragraphs; absolute paths; human voice; WHAT not HOW; no task name; no canary strings; no hints/walkthroughs; env docs realistic without hidden STEP lists; partition caps grounded for verifier.)

### Failure topology
Symptoms cluster under parallel ingest workers: row counts drift, external keys collide, and rollup totals wobble while solo-lane audits pass. The codebase *looks* like idiomatic Spring Data JPA + PostgreSQL — Flyway, chunked REST, `@Transactional` service methods, PL/pgSQL rollup triggers, Hikari pool — but embeds **four coupled boundary violations** of an internal boundary contract, not a single mis-set knob. A property bundle advertises stricter observation-frame semantics while the pool initializer silently downgrades the live JDBC observation frame. The lane writer uses slice-lane flush order (header before line) while the database rollup routine uses child-first acquisition on the rollup lane, inverting lock order under quad bursts. A numeric stamp column sits on the header aggregate while mutations occur on line slices. A post-success coordinator fires retries still inside the commit-frame envelope. Operations notes and `PessimisticAdvice` steer toward isolation bumps and table-wide locks — wrong root cause. The violating edges are stated only in the split HTML boundary corpus using org terminology (**observation frame**, **commit frame**, **slice lane**, **rollup lane**, **post-success envelope**), not in searchable Spring/PostgreSQL doc phrasing agents can pattern-match from training.

### Environment shape
Dockerized PostgreSQL 15 + Maven Spring Boot tree under `/app`: Flyway SQL bundles, PL/pgSQL helpers, JPA entities and repositories under `/app/api/`, lane dispatch and audit bash under `/app/app/`, opaque helpers under `k7m/` and `r8p/`, decoy modules, partition catalog JSON, worker policy TOML, **split HTML boundary-contract corpus (~40 pages, 12 worked examples) under `/app/docs/boundary_contract/`**, `bench_precedence.md`, misleading `operations_notes.md` and `ingest_pipeline.md`. Tests start the API, seed partitions, invoke twenty-two lane scenarios, and parse the audit JSON.


### Test plan
- `test_v1_field` — schema_version equals 1
- `test_label_order` — three family labels in order
- `test_slots_complete` — twenty-two scenario keys exist
- `test_w1_single` — single worker on North-Shelf ingests 3 chunks, no lost rows
- `test_w2_pair` — two parallel workers on North-Shelf cap at 6 active slots without duplicates
- `test_w4_quad` — four workers on East-Crate cap at 10 without unstable totals
- `test_mix_ok` — parallel North + West workers do not cross-taint totals
- `test_deplete_ok` — exact family depletion leaves stable totals without duplicate keys
- `test_backlog_ok` — pipelined chunk simulation stays within caps
- `test_rerun_ok` — replaying workers do not double-insert business keys
- `test_cap_reject` — chunks above family cap return zero accepted records without negative totals
- `test_no_loss` — all rows report lost_rows 0
- `test_global_ok` — stress block reports zero loss events

#### Advanced tests (10 additional — hard, unique, chain-dependent)

- `test_interleave_ab` — alternating chunk posts across North-Shelf and East-Crate in one audit window; each family rollup matches its grounded cap with no cross-family counter bleed (requires flush order + trigger isolation)
- `test_partial_abort_ok` — mid-chunk fault after half the lines persist; audit must show zero accepted for that chunk, no orphan header without lines, and `line_parity_ok` true (requires transaction rollback boundary in `op_n2`, not listener swallow)
- `test_stamp_diverge_guard` — same `external_biz_id` replayed with divergent line payloads within 200ms; exactly one persisted line version and `duplicate_external_keys` 0 (requires stamp on mutated entity + `phase_r8` not re-entering ingest tx)
- `test_snapshot_consistent` — POST chunk then GET partition snapshot within 100ms; response line count must include just-written lines (requires JDBC session aligned with JPA observation profile — `cfg_p9` trap)
- `test_contention_sibling` — quad workers on East-Crate while North-Shelf solo ingest runs concurrently; East stays at 10, North at 6, neither `unstable_totals` (requires `step_w1` lock order + `op_n2` flush order together)
- `test_pool_handoff_ok` — scenario borrows two distinct pool connections for sequential chunks on one family; second chunk must not observe phantom rollup from downgraded session (requires `cfg_p9` init fix alone is necessary but not sufficient without read path fix)
- `test_line_parity_matrix` — for all twenty-two scenario keys, `line_parity_ok` true: accepted line count equals DB line count for that scenario id (catches header-before-line flush orphans)
- `test_race_one_winner` — two workers POST identical `external_biz_id` at the same wall time; DB has exactly one line row and audit `duplicate_external_keys` 0 (requires `phase_r8` AFTER_COMMIT + stamp check + `op_n2` idempotent path)
- `test_monotone_counter` — ordered scenarios `rollup_seq_m` through `rollup_seq_p` on one family: `rollup_monotone` true, counters never decrease (requires `step_w1` trigger not double-subtracting under retry)
- `test_tri_fanout_ok` — three families, three workers, simultaneous four-chunk burst; all three `ingest_compliance` true and caps 6/10/4 honored (integration test — fails if any of four loci partially fixed)

### Hard task calibration (≤20% model pass target)

Target: **≤20% pass rate** on best or worst frontier models. Task must satisfy **all four** platform hard-task pillars:

| Pillar | How this task satisfies it |
|--------|---------------------------|
| **Deep domain expertise** | Spring `@Transactional` + JPA flush ordering + Hikari `connectionInitSql` vs `spring.jpa` isolation + PostgreSQL trigger lock order + transactional event listener phases interact in ways standard tutorials treat separately; fix requires mapping org-reframed **boundary contract** prose to four code/SQL loci. |
| **Complex multi-step reasoning (10+)** | Mandatory **15-step** solver workflow below; skipping dossier reading or fixing one locus fails distinct subsets of 23 tests. |
| **Subtle debugging / non-obvious root cause** | Symptom is lost rows / duplicate keys under parallel lanes while solo replays pass; playbooks blame DB tuning; idiomatic `@Transactional` batch ingest is the surface — root cause is four independent boundary breaks. |
| **Obscure documentation + bespoke rules** | ~40-page HTML corpus reframes JDBC/JPA/PLpgSQL rules; keyword search for `REPEATABLE_READ`, `@Version`, `@TransactionalEventListener` must **not** surface the fix recipe; examples 4/8/11 (reviewer-only IDs) encode observation-frame downgrade and post-success envelope rules. |

**Construction-time LLM shortcut traps (Step 2b must make these fail):**
- Raise `spring.jpa.properties.hibernate.connection.isolation` only → passes `test_w1_single`, fails `test_snapshot_consistent`, `test_pool_handoff_ok`, `test_interleave_ab`
- `@Lock(PESSIMISTIC_WRITE)` on header repo per `operations_notes.md` → reduces flake, fails `test_tri_fanout_ok`, `test_contention_sibling`
- Move `@Version` to line entity without `phase_r8` commit-frame fix → passes `test_stamp_diverge_guard` once, fails `test_race_one_winner`
- Reorder JPA flush only → passes sequential rows, fails `test_w4_quad`, `test_monotone_counter`
- Rewrite `step_w1` only → passes some quad rows, fails `test_line_parity_matrix`, `test_partial_abort_ok`
- Set `Propagation.REQUIRES_NEW` on listener without stamp + pool alignment → fails `test_rerun_ok` and `test_snapshot_consistent`

### INSTRUCTION.mdc alignment (instruction.md only)

| Rule | Commitment |
|------|------------|
| Length | 3 short paragraphs (~120 words); no headers or bullet lists in instruction.md |
| Voice | Human engineer tone; no roleplay, no verifier-centric phrasing, no step-by-step HOW |
| WHAT not HOW | States failing behavior + success criteria + authoritative doc paths only |
| Absolute paths | `/app`, `/app/app/lane_audit.sh`, `/app/output/lane_audit.json`, `/app/docs/boundary_contract/`, `/app/docs/bench_precedence.md` |
| No hints | No isolation enums, annotation names, flush/trigger recipes, fix-path symbols, or 15-step walkthrough in instruction.md |
| Env docs | `boundary_contract/` defines requirements/schemas; `operations_notes.md` is realistic context only — no hidden STEP/HINT walkthroughs (INSTRUCTION.mdc env-files rule) |
| Uniqueness | Parallel chunk-ingest integrity across Spring + PostgreSQL; distinct from meter-NDJSON and RLS tasks |

### Drafting guardrails (environment + code — not instruction.md)

Fix-path symbols opaque (`op_n2`, `phase_r8`, `step_w1`, `cfg_p9`). Boundary HTML uses org-reframed terminology (**observation frame**, **commit frame**, **slice lane**, **rollup lane**) — not copy-paste spring.io/PostgreSQL FAQ phrases. Code symbols must not echo instruction nouns (`code_forbidden_tokens`). Decoy modules perform genuine ancillary work. `operations_notes.md` misdirects but must not contain agent walkthroughs.

### Triviality Ledger

- Setting only `spring.jpa.properties.hibernate.connection.isolation` while Hikari `connectionInitSql` still downgrades the JDBC session passes solo lane but fails dual_lane when workers observe phantom rollup totals.
- Reordering JPA flush to slice-before-header without changing PL/pgSQL rollup lock order passes sequential scenarios but fails quad_lane when the trigger still acquires child locks first.
- Moving the numeric stamp column onto the header entity without wiring the lane writer to bump it passes idempotent replay cosmetically but fails dual_lane when line rows update without stamp checks.
- Registering the post-success coordinator at BEFORE_COMMIT or inside the ingest `@Transactional` method passes solo lane but fails pipe_burst and stress_summary under parallel fan-out.
- Following operations notes to add `@Lock(PESSIMISTIC_WRITE)` on the repository reduces flake rate cosmetically but fails mixed_partitions when flush/rollup inversion remains.
- Fixing only `cfg_p9` session init passes `test_snapshot_consistent` and `test_pool_handoff_ok` but fails `test_interleave_ab` when flush/trigger inversion still cross-taints counters.
- Header-only flush with rollback disabled passes `test_w1_single` but fails `test_partial_abort_ok` and `test_line_parity_matrix` with orphan headers.
- Moving stamp to line entity without `phase_r8` phase fix passes `test_stamp_diverge_guard` cosmetically once but fails `test_race_one_winner` under simultaneous POST.
- Trigger rewrite without monotone guard passes quad scenarios but fails `test_monotone_counter` when retries subtract rollup twice.
- Pessimistic lock on header repository passes `test_contention_sibling` intermittently but fails `test_tri_fanout_ok` under three-family fan-out.

### TASK-QUALITY.mdc alignment (continuous validation)

| Phase | Step 2b gate |
|-------|----------------|
| Phase 1 Idea | Novel parallel-ingest integrity task; multi-step; not one-command; no privileged ops |
| Phase 2 Instruction | Matches INSTRUCTION.mdc draft above; self-contained; fully specified outcomes |
| Phase 3 Environment | Self-contained; offline runtime; no external APIs; data under `/app/data/` |
| Phase 4 Docker | See DOCKER-ENV + DOCKER-IMG sections below |
| Phase 5 Data | All fixtures local; boundary HTML baked in image; no runtime fetch |
| Phase 6 Oracle | `solve.sh` deterministic, offline, reflects instruction outcomes, ≥55 LOC substantive Java/SQL |
| Phase 7 Verifier | 23 deterministic pytest tests; binary reward; no timing tests; matches instruction |
| Phase 8 Env vars | `TEST_DIR` defaults in test harness; no Harbor-only required vars |
| Phase 9 Reserved dirs | Dockerfile must not `mkdir` or `COPY` into `/tests`, `/solution`, `/oracle` |
| Phase 10 Metadata | `task.toml` block below; `allow_internet = false`; single-container (no compose) |
| Phase 11 Pre-submit | Oracle 1× + NOP; reproducible; no hidden solutions in image |

### DOCKER-ENV.mdc alignment

| Rule | Commitment |
|------|------------|
| Dockerfile path | `environment/Dockerfile` only |
| Digest pinning | Every `FROM` uses `@sha256:` digest (builder + runtime) |
| Runtime deps | `tmux` + `asciinema` installed in final image at build time |
| Apt pattern | Single-transaction `apt-get` with `--no-install-recommends` + `rm -rf /var/lib/apt/lists/*` |
| Reproducibility | Pinned apt versions; Maven deps via locked `pom.xml` + `/opt/m2` cache at build |
| COPY ban | Never `COPY solution/` or `COPY tests/`; narrow `COPY` per directory (see DOCKER-IMG) |
| Size | `environment/` ≤100MB total; each file ≤50MB; required `environment/.dockerignore` |
| Offline tests | PostgreSQL, JAR, Flyway, seeded DB, pytest toolchain — all in image before agent runs |
| Compose | **None** — single service in one Dockerfile (not multi-container) |

### DOCKER-IMG.mdc alignment

| Rule | Commitment |
|------|------------|
| Base image | `debian:bookworm-slim@sha256:…` builder/runtime OR sanctioned `postgres:15-bookworm@sha256:…` with Java added — digest-pinned |
| Multi-stage | **Required**: stage `build-api` runs `mvn package`; stage `runtime` ships JAR + JRE + PostgreSQL only |
| Layer order | OS packages → uv/pytest preload → Maven dependency resolve → source `COPY` → `mvn package` → DB init scripts |
| Narrow COPY | `COPY api/pom.xml`, `COPY api/src`, `COPY db/`, `COPY app/`, `COPY lib/`, `COPY data/`, `COPY docs/`, `COPY config/`, `COPY init/` — no `COPY . .` without strict `.dockerignore` |
| `.dockerignore` | Exclude `.git`, `target`, `__pycache__`, `node_modules`, `solution`, `tests`, `*.md` caches |
| OCI labels | `org.opencontainers.image.title`, `.source`, `.licenses`, `.version` on runtime stage |
| Metadata | `chmod -R` forbidden; use `COPY --chmod=0755` on shell scripts |
| Offline | `ENV UV_OFFLINE=1` after build-time uv/pytest warm; `task.toml` `allow_internet = false` |
| Hygiene | No `.git`, secrets, or build tools in final runtime stage |

### REVIEWER-CHECKLIST.mdc compliance (Step 2b)

| Section | Requirement | This task |
|---------|-------------|-----------|
| Instruction | Concise, clear, human, absolute paths, no hints | Three-paragraph draft |
| Environment | Digest pinning, offline, no hidden solutions, .dockerignore | Dockerfile pattern above |
| Oracle | Offline, deterministic, matches instruction | solve.sh patches four loci; reruns lane_audit.sh |
| Verifier | Binary reward, pytest, domain assertions on lane_audit.json | 23 tests; no format-only checks |
| Structure | Non-milestone: env/, solution/, tests/, instruction.md, task.toml | Committed below |
| Metadata | version 2.0, allow_internet=false, resources, tags/languages match | task.toml block |
| Rubric (UI) | ≥3 negatives, no score 4, no test/oracle refs | specs/java-batch-lane-reconcile-rubrics.txt |

### output_contract.toml (Step 2b)

```toml
user_visible_outputs = ["/app/output/lane_audit.json"]

internal_harness_files = [
  "/app/app/lane_audit.sh",
  "/app/data/scenario_matrix.json",
  "/app/data/partition_catalog.json",
  "/app/init/start_api.sh",
]

[structured_outputs.lane_audit]
target = "/app/output/lane_audit.json"
format = "json"
instruction_checks = [
  "schema_version",
  "catalog_partitions",
  "scenarios",
  "ingest_compliance",
  "lost_rows",
  "duplicate_external_keys",
  "unstable_totals",
  "stress_summary",
  "lane_audit.json",
]
```

### task.toml (Step 2b — REVIEWER metadata checklist)

```toml
version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "debugging"
subcategories = ["db_interaction", "tool_specific", "long_context"]
number_of_milestones = 0
codebase_size = "small"
languages = ["java", "sql", "bash"]
tags = ["java", "spring", "postgresql", "jpa", "concurrency"]
expert_time_estimate_min = 120
junior_time_estimate_min = 480

[agent]
timeout_sec = 1800.0

[verifier]
timeout_sec = 900.0

[environment]
build_timeout_sec = 900.0
cpus = 2
memory_mb = 6144
storage_mb = 10240
workdir = "/app"
allow_internet = false
```

No docker-compose. Single container only. No `custom_docker_compose` or `is_multi_container`.

### CI-CHECKLIST.mdc compliance (Step 2b)

| Phase | Requirement | This task |
|-------|-------------|-----------|
| 1 Structural | env/, Dockerfile, tests/test.sh, task.toml, instruction.md | Standard non-milestone layout |
| 2 Instruction | Absolute paths only | `/app/...` in instruction draft |
| 3 Dependencies | Pinned versions, lockfiles | pom.xml + Flyway; pinned apt in Dockerfile; pytest==8.4.1 via uv at build |
| 4 Docker image | Digest pinning, sanctioned base | debian:bookworm-slim@sha256 or postgres:15-bookworm@sha256 |
| 5 Build context | ≤100MB, ≤50MB/file, .dockerignore | Boundary HTML capped; no target/ caches in env |
| 6 Docker hygiene | Clean apt, no upgrade, no chmod -R, layer order | Multi-stage; COPY --chmod for shell scripts |
| 7 Runtime image | No COPY tests/solution; no Dockerfile refs to test_outputs.py or solve.sh | Enforced |
| 8 Verifier | reward.txt always; pytest; binary 0/1; deterministic | Canonical footer below |
| 9 Offline | No runtime pip/curl/apt in test.sh | `ENV UV_OFFLINE=1`; `uvx` only in test.sh |
| 10 Container safety | No privileged, no docker.sock | Single service |
| 11 Metadata | Full task.toml; allow_internet=false | See block above |
| 12 Python | ruff passes on test_outputs.py | Step 2b: `ruff check tasks/.../tests` |

**Final CI validation commands (Step 2b before submit):**
```bash
python3 run_static_checks.py --task-dir tasks/java-batch-lane-reconcile --version edition_2
ruff check tasks/java-batch-lane-reconcile/tests/test_outputs.py
./scripts/check-task.sh tasks/java-batch-lane-reconcile
harbor run -p tasks/java-batch-lane-reconcile -a oracle
harbor run -p tasks/java-batch-lane-reconcile -a nop
```

### Dockerfile pattern (CI Phases 4–7 + REVIEWER environment)

- `FROM debian:bookworm-slim@sha256:<digest>` (builder) + runtime stage with JRE 17 + PostgreSQL 15 — every stage digest-pinned; OCI labels.
- `WORKDIR /app`; `ENV UV_OFFLINE=1` after baking uv cache at build.
- Build-time only: curl uv tarball (checksum-pinned), `UV_OFFLINE=0 uv tool install pytest==8.4.1 --with pytest-json-ctrf==0.3.5`, warm cache with `uvx pytest --version`.
- Runtime apt (pinned, `--no-install-recommends`, rm lists): **tmux**, **asciinema**, **ca-certificates**, **openjdk-17-jdk-headless**, **maven** (build stage only), **postgresql** client/server as required.
- Narrow COPY: api/pom.xml → resolve deps → api/src → db/ → app/ → lib/ → data/ → docs/ → config/ → init/ — never tests/ or solution/.
- `RUN mvn package` in build stage; runtime ships JAR + seeded DB via init scripts.
- `CMD ["sleep", "infinity"]` or entrypoint wrapper starting PostgreSQL + API.
- Forbidden in Dockerfile: `COPY tests`, `COPY solution`, `mkdir /tests`, references to `test.sh`, `test_outputs.py`, `solve.sh`.

### tests/test.sh (CI Phase 8 — canonical offline template)

```bash
#!/bin/bash

# Offline verifier: Dockerfile warms pytest into /opt/uv-cache; UV_OFFLINE=1 at runtime.
source $HOME/.local/bin/env

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
    exit 1
fi

uvx \
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

**CI Phase 8–9 rules:** No `set -euo pipefail`; no apt/curl/pip in test.sh; reward footer exactly 5 lines; no `exit` after `fi`.

### Required artifacts (REVIEWER task structure — non-milestone)

- `instruction.md`, `task.toml`, `output_contract.toml`
- `environment/Dockerfile`, `environment/.dockerignore`, 30+ env files (see Initial Draft Commitments)
- `solution/solve.sh`, `solution/lane-fix.patch` (or inline Java/SQL edits)
- `tests/test.sh`, `tests/test_outputs.py`

### Initial Draft Commitments

- `tasks/java-batch-lane-reconcile/instruction.md`
- `tasks/java-batch-lane-reconcile/task.toml`
- `tasks/java-batch-lane-reconcile/output_contract.toml`
- `tasks/java-batch-lane-reconcile/environment/Dockerfile` (multi-stage; digest-pinned; tmux+asciinema; offline runtime)
- `tasks/java-batch-lane-reconcile/environment/.dockerignore` (excludes solution, tests, target, .git)
- `tasks/java-batch-lane-reconcile/environment/platform/verifier-requirements.txt` (optional; for build-time uv warm)
- `tasks/java-batch-lane-reconcile/environment/init/docker-entrypoint-wrapper.sh`
- `tasks/java-batch-lane-reconcile/environment/init/ensure_pg.sh`
- `tasks/java-batch-lane-reconcile/environment/init/bootstrap.sh`
- `tasks/java-batch-lane-reconcile/environment/init/post_boot.sh`
- `tasks/java-batch-lane-reconcile/environment/init/start_api.sh`
- `tasks/java-batch-lane-reconcile/environment/db/migration/V1__extensions.sql`
- `tasks/java-batch-lane-reconcile/environment/db/migration/V2__core_tables.sql`
- `tasks/java-batch-lane-reconcile/environment/db/migration/V3__rollup.sql`
- `tasks/java-batch-lane-reconcile/environment/db/functions/step_w1.sql`
- `tasks/java-batch-lane-reconcile/environment/db/functions/audit_scalar.sql`
- `tasks/java-batch-lane-reconcile/environment/api/pom.xml`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/resources/application.yml`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/resources/application-prod.yml`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/k7m/cfg_p9.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/k7m/LaneBootstrap.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/r8p/op_n2.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/r8p/LaneController.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/r8p/phase_r8.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/r8p/entity/HeaderSlice.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/r8p/entity/LineSlice.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/r8p/repo/HeaderRepo.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/r8p/repo/LineRepo.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/decoy/PessimisticAdvice.java`
- `tasks/java-batch-lane-reconcile/environment/api/src/main/java/decoy/BatchTuner.java`
- `tasks/java-batch-lane-reconcile/environment/app/lane_audit.sh`
- `tasks/java-batch-lane-reconcile/environment/app/scenario_a.sh` through `scenario_l.sh`
- `tasks/java-batch-lane-reconcile/environment/app/scenario_m.sh` through `scenario_v.sh`
- `tasks/java-batch-lane-reconcile/environment/lib/psql_wrap.sh`
- `tasks/java-batch-lane-reconcile/environment/lib/curl_wrap.sh`
- `tasks/java-batch-lane-reconcile/environment/lib/result_collect.sh`
- `tasks/java-batch-lane-reconcile/environment/data/partition_catalog.json`
- `tasks/java-batch-lane-reconcile/environment/data/scenario_matrix.json`
- `tasks/java-batch-lane-reconcile/environment/config/worker_policy.toml`
- `tasks/java-batch-lane-reconcile/environment/docs/bench_precedence.md`
- `tasks/java-batch-lane-reconcile/environment/docs/boundary_contract/index.html`
- `tasks/java-batch-lane-reconcile/environment/docs/boundary_contract/part_02.html`
- `tasks/java-batch-lane-reconcile/environment/docs/boundary_contract/part_03.html`
- `tasks/java-batch-lane-reconcile/environment/docs/boundary_contract/part_04.html`
- `tasks/java-batch-lane-reconcile/environment/docs/boundary_contract/part_05.html`
- `tasks/java-batch-lane-reconcile/environment/docs/boundary_contract/examples.html`
- `tasks/java-batch-lane-reconcile/environment/docs/boundary_contract/glossary.md`
- `tasks/java-batch-lane-reconcile/environment/docs/operations_notes.md`
- `tasks/java-batch-lane-reconcile/environment/docs/ingest_pipeline.md`
- `tasks/java-batch-lane-reconcile/environment/decoy/n8f_metrics.sql`
- `tasks/java-batch-lane-reconcile/solution/solve.sh`
- `tasks/java-batch-lane-reconcile/solution/lane-fix.patch`
- `tasks/java-batch-lane-reconcile/tests/test.sh`
- `tasks/java-batch-lane-reconcile/tests/test_outputs.py`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table

```
- path: environment/api/src/main/java/r8p/op_n2.java
  symbol: op_n2
  kind: method
  signature: public IngestResult op_n2(String label, List<RowPayload> chunk)
  purpose: persists a chunked ingest for a catalog label with flush boundaries

- path: environment/api/src/main/java/r8p/phase_r8.java
  symbol: phase_r8
  kind: class
  signature: @Component class phase_r8 implements ApplicationListener<LaneCommittedEvent>
  purpose: schedules follow-up work when a lane chunk reports success

- path: environment/db/functions/step_w1.sql
  symbol: step_w1
  kind: function
  signature: step_w1() RETURNS trigger LANGUAGE plpgsql
  purpose: maintains partition rollup counters on line mutations

- path: environment/api/src/main/java/k7m/cfg_p9.java
  symbol: cfg_p9
  kind: constant
  signature: @Bean HikariDataSource cfg_p9(DataSourceProperties props)
  purpose: builds the runtime pool with session initializer hooks
```

#### flipping_point_contract

```
locations:
  - id: A
    path: environment/api/src/main/java/r8p/op_n2.java
    controls_tests: [test_w2_pair, test_w4_quad, test_backlog_ok, test_mix_ok, test_global_ok, test_interleave_ab, test_partial_abort_ok, test_line_parity_matrix, test_race_one_winner, test_snapshot_consistent, test_tri_fanout_ok]
  - id: B
    path: environment/api/src/main/java/r8p/phase_r8.java
    controls_tests: [test_w1_single, test_rerun_ok, test_cap_reject, test_no_loss, test_partial_abort_ok, test_stamp_diverge_guard, test_race_one_winner]
  - id: C
    path: environment/db/functions/step_w1.sql
    controls_tests: [test_deplete_ok, test_label_order, test_slots_complete, test_contention_sibling, test_monotone_counter, test_tri_fanout_ok]
  - id: D
    path: environment/api/src/main/java/k7m/cfg_p9.java
    controls_tests: [test_v1_field, test_mix_ok, test_snapshot_consistent, test_pool_handoff_ok, test_tri_fanout_ok]
no_single_location_flips_majority: true
concentration_cap: 0.5
```

#### decoy_manifest

```
- path: environment/api/src/main/java/decoy/PessimisticAdvice.java
  kind: module
  rhymes_with: op_n2
  non_fix_purpose: documents table-wide lock acquisition patterns referenced in operations notes

- path: environment/api/src/main/java/decoy/BatchTuner.java
  kind: module
  rhymes_with: cfg_p9
  non_fix_purpose: adjusts batch size and fetch depth for reporting queries only

- path: environment/decoy/n8f_metrics.sql
  kind: helper
  rhymes_with: step_w1
  non_fix_purpose: nightly rollup metrics snapshot not on ingest hot path
```

#### code_forbidden_tokens

```
code_forbidden_tokens: [spring, boot, chunk, ingest, service, loses, rows, duplicates, business, keys, whenever, parallel, uploads, single-threaded, replays, north-shelf, east-crate, west-bin, lane_audit, read, report, judge, playbooks, database, tuning, qa, thinks, breaking, several, invariants, boundary, material, disagrees, playbook, follow, bench_precedence, conflict, need, every, scenario, lost, duplicate, external, stable, rollup, totals, ingest_compliance, fine, still, look, stress_summary, block, should, end, those, families]
```
