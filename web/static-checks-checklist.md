# Static Checks & Submission Checklist

Use this checklist whenever you are:

- shaping a draft into a real task
- fixing static-check or CI issues
- packaging a submission zip
- deciding whether a task is actually ready for repo-local validation

This file is the final preflight inside the standalone bundle.

## Required Preflight Commands

Before you say a task is ready, run the relevant local commands in the real repo environment:

```bash
bash ci_checks/check-no-canary.sh
bash ci_checks/check-dockerfile-sanity.sh
bash ci_checks/check-test-sh-sanity.sh
bash ci_checks/validate-task-fields.sh
bash ci_checks/check-test-file-references.sh
bash ci_checks/check-dockerfile-references.sh
bash ci_checks/check-task-absolute-path.sh
harbor run -p "tasks/<task-name>" -a oracle
harbor run -p "tasks/<task-name>" --agent nop
python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2
```

If `ruff` is available, also run:

```bash
ruff check tasks/<task-name>
```

Rules for reporting:

- if you scope a check to one task, say so explicitly
- if you skip a check, say why
- if local checks pass but the stricter envgen/static checker disagrees, treat the stricter checker as authoritative

## Manual Instruction ↔ Verifier Parity Pass

Before declaring success, do a manual parity sweep:

- every explicit route, CLI action, output file, schema, and persistence guarantee in `instruction.md` must have a corresponding test
- every exact verifier assumption that matters for correctness must be disclosed in `instruction.md`
- if tests assert exact literals such as header names, cookie names, enums, or fixed messages, either document them or loosen the tests
- every tested upsert, replace, dedupe, delete, and invalid-case rule should be explicit in `instruction.md`
- read verifier setup helpers too; hidden `/health` routes or undocumented support contracts still count as task requirements
- if timestamps or similar serialized values matter, either specify the exact format or make the verifier tolerant
- if normalization can turn a value invalid after trim/lowercasing, state that explicitly and test it directly
- if hashes or content addresses are promised, document the canonical bytes/normalization and verify the real digest rather than just its shape
- if defaults affect hashing, dedupe, or persisted structure, test both omitted-input and explicit-default forms
- if the task has staged vs active or another two-phase state model, test at least one intermediate state directly
- scan the tests for dead fallback branches or tautological assertions
- scan `instruction.md` for dense requirement piles and split them into more readable prose or light bullets if needed

## `task.toml` Gate

- `version` must be `"2.0"`
- use `task.toml`, not `task.yaml`
- put metadata under `[metadata]`
- keep `[agent]`, `[verifier]`, and `[environment]` as separate tables

Required `[metadata]` keys:

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

Validation rules:

- `author_name` should be `anonymous`
- `author_email` should be `anonymous`
- `difficulty` must be exactly `easy`, `medium`, or `hard`
- final difficulty claims should be based on the better-performing frontier model across 5 runs per model
- `easy` is blocked for acceptance
- Python tasks are accepted only when the empirical difficulty is `hard`
- `category` must be one of the allowed repo categories
- `languages`, `tags`, `codebase_size`, `number_of_milestones`, and `subcategories` must all be present and valid
- `codebase_size` must be `minimal`, `small`, or `large`, but accepted tasks should end up `small` or `large`
- keep `tags` to 3-6 descriptive values without obvious filler
- always include `subcategories`
- the safe default is `subcategories = []`
- accepted `subcategories` values are:
  - `api_integration`
  - `db_interaction`
  - `long_context`
  - `tool_specific`
  - `ui_building`
- do not use `long_context` unless the task truly requires at least 50k tokens of reading, roughly 50-150 pages, and semantic reasoning rather than simple parsing/search
- do not use `api_integration` unless the API is mocked locally in Docker with no external web access
- do not use `ui_building` unless the task is genuinely UI-facing and aligned to the UI verifier stack rather than ordinary pytest-only validation
- if Python is used as the main implementation language, make sure that choice is justified rather than just being the default
- if FastAPI is used, make sure that choice is justified rather than accidental or habitual
- if the task materially depends on specialized CLIs, SDKs, or libraries such as `capsh`, `strace`, `libcap`, `ffmpeg`, or `graphviz`, include `tool_specific`
- do not use unsupported metadata keys such as `task_subtypes`
- do not include `task_id`
- if `environment/docker-compose.yaml` exists, set `custom_docker_compose = true` under `[metadata]`
- if that compose file defines multiple services, also set `is_multi_container = true`

`[environment]` must include positive integers for:

- `cpus`
- `memory_mb`
- `storage_mb`
- `build_timeout_sec`

## `tests/test.sh` Gate

- use `set -euo pipefail` near the top unless there is a documented shell-specific reason not to
- initialize the reward file before other fallible commands:

```bash
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
```

- add the `WORKDIR` guard near the top:

```bash
if [ "$PWD" = "/" ]; then
  echo "Error: No WORKDIR set. Add WORKDIR to the Dockerfile." >&2
  exit 1
fi
```

- keep verifier dependencies in `tests/test.sh`, not the Dockerfile
- network installs in `tests/test.sh` are allowed
- if only the verifier needs Python, `uv`, `pytest`, `pytest-json-ctrf`, Node, `openssh-client`, `ssh`, `sftp`, `curl`, `jq`, or similar tooling, install them here instead of the image
- pin verifier tooling versions where practical
- if network-installed verifier tooling is used, keep `[verifier] timeout_sec` at `300` or higher
- oracle and agent runs must use identical test logic

### Exact reward footer

`tests/test.sh` must end with this exact literal block, with nothing after it:

```bash
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
```

Do not replace `$?` with a custom variable in the final footer.

### Python verifier entrypoint

For standard Python verifiers, the maintained pattern is pytest under `uv`:

- `uvx --with pytest==8.4.1 pytest /tests/test_outputs.py -rA`
- `uvx --with pytest==8.4.1 --with pytest-json-ctrf==0.3.5 pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA`
- `uv pip install pytest==...` followed by `uv run pytest /tests/test_outputs.py -rA`

Do not use:

- `python3 /tests/test_outputs.py`
- custom `__main__` runners
- custom discovery drivers for standard Python verifiers

For milestone Python verifiers, apply the same rule to `test_m1.py ... test_mN.py`.

## Dockerfile Gate

- pin every Docker `FROM` stage by digest
- leave apt packages unversioned in this repo
- pin application dependencies clearly and inspectably
- copy requirements or lockfiles before install so the checker can see them
- if `environment/docker-compose.yaml` exists, pin every referenced image there too
- do not copy `solution/` or `tests/` into the image
- keep verifier-only dependencies out of the image
- set `WORKDIR` explicitly
- do not create reserved paths such as `/tests`, `/solution`, or `/oracle`
- do not use privileged mode, `SYS_ADMIN`, or `docker.sock`
- do not escape the `environment/` directory in the build context
- keep runtime assets in `environment/`
- do not rely on runtime web fetches for task data

## Instruction & File Hygiene Gate

- use absolute paths in `instruction.md`
- keep `instruction.md` concise and human-written
- avoid canned benchmark sections like `Deliverables`, `Artifacts`, or `Acceptance Criteria` unless the task genuinely needs them
- if `instruction.md` has many distinct requirements, add enough visual separation to keep it scannable
- if the task claims `long_context`, `api_integration`, or `ui_building`, make sure the task contract honestly reflects the subtype constraints rather than only carrying the label in metadata
- do not include the task name
- do not include canary strings
- do not mention a specific tool unless the verifier can prove it
- do not leave generated artifacts in the task tree
- exclude `__pycache__/`, `.pyc`, temp files, and local logs from the zip
- do not ship gold outputs or expected final states in agent-visible files
- hidden-case bundles created inside the verifier must still contain inputs only
- if `instruction.md` promises structured artifacts, parse and validate those artifacts directly in tests
- if those artifacts contain object/dict/map fields and the verifier depends on the exact keys, document and validate the key format too
- if the contract names a concrete digest/content-address algorithm, verify the actual digest rather than only a regex or length
- do not enforce performance with wall-clock assertions
- make sure Python test modules expose discoverable `test_...` functions when the tooling expects them

## Milestone Gate

For milestone tasks:

- include `milestone_1.md ... milestone_N.md` at the task root
- `milestone_1.md` must include the overall intro plus Milestone 1
- later milestone files must contain only their own milestone descriptions
- include `solve1.sh ... solveN.sh`
- include `test_m1.py ... test_mN.py`
- each milestone test must score only that milestone, not future work

## Submission Zip Gate

- put the archive in `Task_Ready_To_Submit/`
- the filename must be exactly `<task-name>.zip`
- zip the contents of the task directory, not the enclosing directory
- after packaging, inspect the archive and confirm that `instruction.md`, `task.toml`, `environment/`, `solution/`, and `tests/` are at the archive root

Suggested packaging pattern:

```bash
cd tasks/<task-name>
zip -rq /abs/path/Task_Ready_To_Submit/<task-name>.zip . -x '*/__pycache__/*' '*.pyc'
unzip -l /abs/path/Task_Ready_To_Submit/<task-name>.zip
```

## Final Rule

Do not say a task is ready, clean, or submission-safe until:

- oracle and nop were actually run
- the relevant static checks were actually run
- the manual parity pass above was actually done
