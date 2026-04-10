# Terminal-Bench 3.0 Edition 2 — Standalone Task Creation Guide

Use this file as the canonical authoring reference inside the standalone `web` bundle.

- If any older note or example conflicts with this guide, follow this guide.
- This guide is synced to the current active authoring rules.
- If the active rules are silent or ambiguous on a point, prefer the stricter interpretation already stated elsewhere in this bundle. If the bundle still does not resolve it, flag the ambiguity instead of inventing a new rule.
- The only intentional bundle-level override is that early ideation may default difficulty to `hard` unless the user explicitly asks for another label. That is a drafting shortcut, not final validation.

## Intake Rules

### Repo-faithful required inputs

When you are trying to turn an idea into an actual task draft, these are the important inputs:

1. **Task idea**
   What should the task accomplish? What problem should the agent solve?

2. **Programming language(s)**
   Use the primary implementation languages the task actually needs.

3. **Difficulty**
   In the real repo workflow this should be `medium` or `hard`, and the final label must be supported empirically.

4. **Category**
   Allowed values:
   - `system-administration`
   - `build-and-dependency-management`
   - `data-processing`
   - `games`
   - `software-engineering`
   - `machine-learning`
   - `debugging`
   - `security`
   - `scientific-computing`

5. **Task name**
   A short kebab-case directory name such as `distributed-trace-analysis`.

6. **UI / multi-container confirmation when relevant**
   Confirm whether the task is truly a UI task or truly needs docker-compose / multiple services, because those choices change the required layout.

### Optional inputs

- `subcategories`
  Use only the recognized Edition 2 values:
  - `api_integration`
  - `db_interaction`
  - `long_context`
  - `tool_specific`
  - `ui_building`

- `number_of_milestones`
  Use `0` for non-milestone tasks. Use milestone structure only when it is genuinely needed.

### Fixed values for this standalone bundle

- `author_name = "anonymous"`
- `author_email = "anonymous"`
- `version = "2.0"`
- drafting default: `difficulty = "hard"` unless the user explicitly overrides it

If you use the bundle-level `hard` default during ideation, still treat the final difficulty label as provisional until benchmarked.

## Current Acceptance Gates

Apply these gates while shaping the task:

- `minimal` codebase size is blocked; accepted tasks should use `small` or `large`
- `easy` difficulty is blocked; accepted tasks should use `medium` or `hard`
- Python tasks are accepted only when the empirical difficulty is `hard`
- during ideation, avoid Python unless there is a compelling reason to choose it
- prefer single-container tasks; multi-container should be rare and justified
- avoid FastAPI during ideation unless there is a compelling reason to choose it
- `api_integration` tasks must mock the API locally in Docker with no external web dependency
- `long_context` tasks must require at least 50k tokens of reading, roughly 50-150 pages, and semantic reasoning; do not fake this with simple parsing or keyword search

## Recommended Workflow

1. Screen the idea with `TASK_PROPOSAL_RUBRIC.md`.
2. Use `chatgpt-task-authoring-playbook.md` plus the kickoff template for ideation and first-pass drafting.
3. Draft the task files using the rules in this guide.
4. Before calling the task ready, apply `static-checks-checklist.md`.

Do not claim a task is ready to submit unless the real local commands were run in the repo environment.

## Task Structure

### Standard non-UI, non-milestone task

```text
tasks/<task-name>/
├── instruction.md
├── task.toml
├── environment/
│   └── Dockerfile
├── solution/
│   └── solve.sh
└── tests/
    ├── test.sh
    └── test_outputs.py
```

### Milestone task

```text
tasks/<task-name>/
├── instruction.md
├── task.toml
├── milestone_1.md
├── milestone_2.md
├── ... milestone_N.md
├── environment/
│   └── Dockerfile
├── solution/
│   ├── solve.sh
│   ├── solve1.sh
│   ├── solve2.sh
│   └── ... solveN.sh
└── tests/
    ├── test.sh
    ├── test_m1.py
    ├── test_m2.py
    └── ... test_mN.py
```

### UI task

UI tasks use a different verifier stack. If the task is truly UI-heavy, include the maintained UI verifier structure rather than improvising a one-off layout. UI tasks are validated with the UI verifier stack and Playwright-style testing, not the usual pytest-only validators. Unless the task is also a true milestone task, keep `number_of_milestones = 0`.

A typical UI task adds files such as:

- `tests/README.md`
- `tests/package.json`
- `tests/playwright.config.ts`
- `tests/vitest.config.ts`
- `tests/unit/*.spec.ts`
- `tests/e2e/*.spec.ts`
- any real app files needed to serve the UI

Placeholder UI scaffolding is not acceptable. The app under test must be the real task target.

### Subcategory guardrails

- `long_context` is only appropriate when the task truly depends on at least 50k tokens of reading, roughly 50-150 pages, and semantic reasoning. If simple parsing, filtering, or keyword search is enough, do not label it `long_context`.
- `api_integration` is only appropriate when the API is mocked locally in Docker with no external web access. If the task depends on a live remote API, do not label it `api_integration`.
- `ui_building` is only appropriate for genuine UI tasks that use the UI verifier stack rather than ordinary pytest-only backend validation.

## Submission Zip Rules

- Put the final archive in `Task_Ready_To_Submit/`.
- The filename must be exactly `<task-name>.zip`.
- Zip the contents of the task directory, not the enclosing directory.
- After extraction, `instruction.md`, `task.toml`, `environment/`, `solution/`, and `tests/` must sit directly at the archive root.
- Do not include `rubrics.txt` or `rubric.txt`; rubric text belongs in the platform UI.

## `instruction.md`

`instruction.md` is the primary user-facing prompt for the agent.

### Required style

- write like a real engineer asking a coding agent for help
- keep it concise and natural
- avoid synthetic benchmark scaffolding such as `Deliverables`, `Artifacts`, `Acceptance Criteria`, or similar default headings unless the task genuinely needs them
- avoid dense wall-of-text prompts; if the task has many requirements, use light bullets or short sections for scanability
- give the agent the **what**, not the **how**
- do not include hints, solution guidance, rubrics, or step-by-step answer paths
- do not include the task name
- do not include canary strings
- do not require a specific tool unless the verifier can really prove that tool usage

### Contract requirements

- use in-container absolute paths only, such as `/app/output.json`
- explicitly name every output file or modified file the verifier checks
- if the task promises structured output, document the schema directly in `instruction.md`
- if that structured output contains object/dict/map fields and the verifier depends on the exact keys, document the key format too
- if the verifier depends on exact literals such as header names, cookie names, enums, or fixed user-facing messages, either document those literals or loosen the verifier
- every explicit requirement or prohibition in `instruction.md` must get direct verifier coverage
- for security and hardening tasks, test each named restriction directly instead of relying on one broad smoke test

### Milestone requirements

For milestone tasks:

- `instruction.md` must include the overall intro plus the description of every milestone
- it must tell the agent to signal completion before moving to the next milestone
- `milestone_1.md` must include the overall intro plus Milestone 1
- `milestone_2.md` through `milestone_N.md` must contain only their own milestone descriptions

## `task.toml`

### Required structure

- `version = "2.0"` at the top level
- put author/task metadata under `[metadata]`
- keep `[agent]`, `[verifier]`, and `[environment]` as separate tables
- do not use `task.yaml`

### Required `[metadata]` keys

- `author_name`
- `author_email`
- `category`
- `difficulty`
- `tags`
- `languages`
- `codebase_size`
- `number_of_milestones`
- `subcategories`
- `expert_time_estimate_min`
- `junior_time_estimate_min`

### Metadata rules

- `author_name = "anonymous"`
- `author_email = "anonymous"`
- `category` must be one of the allowed values listed above
- `difficulty` must be `easy`, `medium`, or `hard`, but accepted tasks should end up `medium` or `hard`
- this standalone bundle may draft ideas as `hard` by default, but final difficulty still needs empirical support
- `languages` must reflect the task honestly
- `codebase_size` must be `minimal`, `small`, or `large`, but accepted tasks should end up `small` or `large`
- `number_of_milestones` must be `0` for non-milestone tasks or the exact milestone count for milestone tasks
- `subcategories` must always be present
- the safe default is `subcategories = []`
- do not invent free-form subcategory values
- do not use `task_subtypes`
- do not include `task_id`
- keep `tags` to 3-6 descriptive values and avoid obvious redundancy

### Compose flags

If `environment/docker-compose.yaml` exists:

- set `custom_docker_compose = true` under `[metadata]`
- if multiple services are defined, also set `is_multi_container = true`

### Environment resource keys

Under `[environment]`, include positive integers for:

- `cpus`
- `memory_mb`
- `storage_mb`
- `build_timeout_sec`

Common defaults are `cpus = 2`, `memory_mb = 4096`, and `storage_mb = 10240`, but increase them when the task genuinely needs more.

## `environment/Dockerfile`

### Core rules

- pin every `FROM` stage by digest
- leave apt packages unversioned in this repo; do not add apt version pinning
- pin non-apt application dependencies clearly and inspectably
- copy requirements or lockfiles before install so static checks can see what is being installed
- set `WORKDIR` explicitly
- do not copy `solution/` or `tests/` into the image
- do not create reserved paths like `/tests`, `/solution`, or `/oracle`
- do not install verifier-only dependencies in the image
- do not use privileged containers, `SYS_ADMIN`, or `docker.sock`
- keep runtime assets under `environment/`
- do not escape the `environment/` build context
- do not require runtime web fetches for task data

### Dependency placement

- agent/runtime dependencies belong in the image
- verifier-only dependencies belong in `tests/test.sh`
- if the task code itself does not need Python, `uv`, `pytest`, Node, or similar tooling, keep them out of the Dockerfile

### Build-context validation

Local Harbor and some evaluators may build slightly differently. Before submission, validate the intended build path and do not "fix" portability by violating the `environment/` boundary.

## `solution/solve.sh`

- `solution/solve.sh` is required
- it must solve the full task deterministically
- it must perform real work rather than copying expected outputs from visible references
- it should fail fast
- it should not hang on interactive editors
- it should not fetch web dependencies at solve time

For milestone tasks:

- include `solve1.sh ... solveN.sh`
- make `solution/solve.sh` chain them in order
- each milestone oracle may assume previous milestones are already complete

## `tests/test.sh`

### Core rules

- use `set -euo pipefail` near the top unless there is a documented shell-specific reason not to
- initialize the reward file before other fallible setup:

```bash
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
```

- add a `WORKDIR` guard near the top:

```bash
if [ "$PWD" = "/" ]; then
  echo "Error: No WORKDIR set. Add WORKDIR to the Dockerfile." >&2
  exit 1
fi
```

- keep verifier dependencies in `tests/test.sh`, not the Dockerfile
- network installs in `tests/test.sh` are allowed
- pin verifier tooling versions where practical
- if `tests/test.sh` installs verifier tooling from the network, use `[verifier] timeout_sec = 300` or higher
- oracle and agent runs must use identical test logic

### Required reward footer

`tests/test.sh` must end with this exact literal block, with nothing after it:

```bash
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
```

Do not replace `$?` with another variable in the final footer.

### Python verifier entrypoint

For standard Python verifiers, run pytest under `uv`, not plain `python3`.

Accepted patterns include:

- `uvx --with pytest==8.4.1 pytest /tests/test_outputs.py -rA`
- `uvx --with pytest==8.4.1 --with pytest-json-ctrf==0.3.5 pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`
- `uv pip install pytest==...` followed by `uv run pytest /tests/test_outputs.py -rA`

Do not use:

- `python3 /tests/test_outputs.py`
- custom `__main__` runners
- custom discovery wrappers that bypass pytest as the entrypoint

For milestone Python verifiers, apply the same rule to `test_m1.py ... test_mN.py`.

## `tests/test_outputs.py`

- use the exact filename `test_outputs.py`
- verify observable behavior, not hidden implementation details
- add informative docstrings to every test function
- ensure each explicit behavior in `instruction.md` has corresponding tests
- ensure every tested behavior is disclosed in `instruction.md`
- prefer structured assertions over brittle full-string equality
- include anti-cheating measures
- avoid wall-clock and hardware-sensitive assertions
- keep the module lint-clean
- expose discoverable top-level `test_...` functions when the tooling expects them

## Milestone Verifiers

For milestone tasks:

- use `tests/test_m1.py ... tests/test_mN.py`
- each `test_mX.py` should score only milestone `X`, not future milestones
- milestone tests may assume prior milestone state already exists
- milestone tests follow the same behavior-first, docstring, anti-cheating, and determinism rules as `test_outputs.py`

## UI Verifiers

If the task is a real UI task:

- success should require both unit and E2E checks
- align `tests/package.json` scripts with `tests/test.sh`
- point Playwright at the real served app, not a placeholder
- replace placeholder DOM assertions with real user-observable behavior
- replace placeholder app content with the real required UI

## Rubric Workflow

- do not include a rubric file in the zip
- rubric text belongs in the platform UI
- valid rubric scores are only `+1`, `+2`, `+3`, `+5`, `-1`, `-2`, `-3`, and `-5`
- an initial submission should generate the rubric without sending to reviewer
- after CI passes and the rubric is edited, submit again without regenerating the rubric so you do not overwrite manual edits

## Difficulty Evaluation

Final difficulty is based on the **better-performing** frontier model across repeated runs.

- use 5 runs per model before locking the label
- `hard` means the better-performing model passes at most 20%
- `medium` means the better-performing model passes 21-80%
- `easy` means the better-performing model passes above 80% and is blocked for acceptance
- if frontier models pass 100%, the task is too trivial

The standalone bundle may still draft ideas as `hard` by default during ideation. That default is not a substitute for real benchmarking.

## Validation Commands

Use these in the real repo environment when validating the draft:

```bash
harbor run -p "tasks/<task-name>" -a oracle
harbor run -p "tasks/<task-name>" --agent nop
harbor tasks start-env -p "tasks/<task-name>" -e docker -a -i
python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2
```

If available, also run:

```bash
ruff check tasks/<task-name>
```

Use `static-checks-checklist.md` as the final preflight before claiming the task is ready.

## Key Reminders

- keep the task hard for a good reason
- do not let hidden-instance discovery be the main source of difficulty
- do not leak answers through agent-visible files
- keep verifier-only tooling in `tests/test.sh`
- keep the instruction honest about what the verifier checks
- do not claim submission readiness until oracle, nop, and static checks really ran
