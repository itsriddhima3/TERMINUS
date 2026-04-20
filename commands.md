# Commands Reference

All harbor, CI, validation, and debug commands for Terminal-Bench 3 task development.

## Harbor — Task Validation

```bash
# Preflight: oracle and NOP may be launched in parallel in separate terminals
# as long as task files are not being edited during the run.
# Oracle stress test — 10 parallel runs (no API key needed)
harbor run -p "tasks/<task-name>" -a oracle -k 10 -n 10

# NOP (must score 0.0, no API key needed)
harbor run -p "tasks/<task-name>" -a nop

# Only after BOTH oracle and NOP pass:
# Source OpenAI API key (required for the GPT-5.2 quality check)
set -a && source .env && set +a

# Quality check (uses the OpenAI API via harbor)
harbor tasks check "tasks/<task-name>" -m "openai/gpt-5.2"

# Interactive debug (shell into the container)
harbor tasks start-env -p "tasks/<task-name>" -e docker -a -i

# Init new task skeleton
harbor tasks init <task-name> --include-standard-metadata --tasks-dir tasks/
```

### Parallel execution notes

- `-k N` sets how many parallel runs to schedule; use `-n N` to cap how many run at once
- Oracle: use `-k 10 -n 10` so all 10 runs execute together (no buffered batches)
- Each parallel run gets its own job directory, results are aggregated automatically
- `oracle -k 10 -n 10` and `nop` are safe to run at the same time as preflight in separate terminals
- Do not start quality check until both preflight runs have passed
- Do not overlap `verifier_health.py` with real Step 3a harbor runs on the same task directory; it launches additional oracle jobs and temporary task copies for randomized-order and partial-oracle checks

### Interpreting results

- **Mean 1.0** = agent passed all tests (for oracle runs, this is expected)
- **Mean 0.0** = agent failed all tests (expected for NOP)
- **Errors** = agent crashed before producing a result (infra issue, not task issue)
- Difficulty is judged by the mechanical stack (collapse check RC1-RC7 + verifier_health). Repo-local approval uses only that stack plus packaging checks.

## Git (Temporary Local Init)

```bash
# Initialize git locally (needed for some harbor/CI commands)
cd <project-root>
git init
git add .
git commit -m "local workspace init"

# After pushing to main repo, clone from there instead:
# git clone https://github.com/<your-fork>/terminal-bench-3.git
```

## CI / Static Checks

```bash
# Use these while authoring and debugging.
# Edition 2 task-scoped static checker for repo-local structural/compliance rules
python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2

# Focused subsets when debugging one area
python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2 --only task_toml --only task_structure
python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2 --only dockerfile --only compose
python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2 --only test_sh --only test_layout
python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2 --only instruction --only absolute_paths --only canary --only output_contract

# Legacy ci_checks/*.sh entrypoints are compatibility wrappers only. They delegate
# to run_static_checks.py and are no longer the source of truth for per-task semantics.
# NOTE: run_static_checks.py does NOT run collapse_check.py or the Harbor quality check,
# and it does not determine approval on its own.
# It covers the repo-local static rule set only.

# Lint test file
ruff check tasks/<task-name>/tests/
```

### Diff your task against a reference task

```bash
# Compare the static-check output of an in-progress task against a known-clean
# reference task from Task_Ready_To_Submit/. The reference task should have at
# most the same warnings yours does (and ideally the same number).
# See Task_Ready_To_Submit/REFERENCE.md for which reference task fits your pattern.

REF=rollback-replay-divergence  # or another zip from Task_Ready_To_Submit/
unzip -q -o Task_Ready_To_Submit/${REF}.zip -d /tmp/ref/
diff <(python3 run_static_checks.py --task-dir tasks/<task-name> 2>&1 | grep '^  -' | sort) \
     <(python3 run_static_checks.py --task-dir /tmp/ref/${REF}    2>&1 | grep '^  -' | sort)
```

## Verifier Health

```bash
# Machine-run verifier health gate for review-time checks.
# This runs repeated oracle consistency, randomized-order verifier runs,
# and partial-oracle ablations, then writes a JSON report for approve_task.py.
python3 verifier_health.py --task-dir tasks/<task-name> --output-json /tmp/<task-name>-verifier-health.json

# Optional machine-readable stdout form.
python3 verifier_health.py --task-dir tasks/<task-name> --json
```

`verifier_health.py` uses temporary task copies so it can mutate `solve.sh` and `tests/test.sh` safely for automation, and it distinguishes verifier-backed behavioral failures from compile-only partial-oracle failures. Compile-only ablations do not count as verifier discrimination.

## Hard Approval Gate

The mechanical stack (static checks, collapse check RC1-RC7, verifier_health, submission zip, manifests, zip/source parity) is the sole approval gate.

```bash
# Standard invocation.
python3 approve_task.py --task-dir tasks/<task-name> --zip Task_Ready_To_Submit/<task-name>.zip --verifier-health /tmp/<task-name>-verifier-health.json

# Machine-readable JSON.
python3 approve_task.py --task-dir tasks/<task-name> --zip Task_Ready_To_Submit/<task-name>.zip --verifier-health /tmp/<task-name>-verifier-health.json --json
```

`approve_task.py` is the authoritative repo-local hard-task approval gate. It consumes the verifier-health report and bundles `run_static_checks.py`, `collapse_check.py` (RC1-RC7), `validate_submission_zip.py`, manifest verification, and zip/source parity. Exit 0 is required before calling a hard task approved or ready in this repo.

## Repo Tooling Regressions

```bash
# Repo-level regression suite for run_static_checks.py, collapse_check.py,
# verifier_health.py, and approve_task.py against the checked-in task and
# synthetic fixtures.
python3 -m repo_tests
```

Any future checker fix for a false positive or false negative should update this suite in the same change.

## Collapse & Discoverability Check

```bash
# Mechanical collapse/discoverability check (run after Step 2b and during Step 3b)
python3 collapse_check.py tasks/<task-name>

# JSON output (for CI integration)
python3 collapse_check.py tasks/<task-name> --json
```

Exit codes: `0` = PASS, `1` = FAIL (blocking), `2` = WARN (needs justification).

Checks seven root causes of task triviality:

1. **RC1 Oracle Simplification** — does the fix mostly REMOVE code rather than ADD logic?
2. **RC2 Oracle Predictability** — can visible signals (instruction, file names, test names) predict oracle targets?
3. **RC3 Verifier Shallowness** — do tests check format/schema/existence, or domain-correct computed values?
4. **RC4 Tamper Surface** — can the agent modify what tests depend on to bypass domain reasoning?
5. **RC5 Reference Artifacts** — are answer-shaped golden/reference/broken fixtures visible on solver-visible file surfaces?
6. **RC6 Instruction Specificity** — does `instruction.md` already specify the fix? Delegates to `instruction_audit.py` which scores six signal families (named algorithms, schema enumerations, API/CLI enumerations, numeric thresholds, binding phrases, scope closures) and classifies the instruction as `spec-complete` / `cause-revealing` / `symptoms-only`.
7. **RC7 Oracle Triviality** — is the oracle's non-boilerplate LOC below the A12 sanity floor? FAIL if <30, WARN if 30-80, PASS at 80+.

Solver-visible file surfaces per `@task-creation.mdc`: `instruction.md`, `tests/`, and `environment/`; `task.toml` and `output_contract.toml` are authoring/package metadata and not modeled as solver-visible.

The oracle/frontier checks are transitive: `collapse_check.py` follows `solution/solve.sh`, solution-local called scripts, `patch -p1 < file.patch`, heredoc writes, in-place shell rewrites (`sed -i`, `perl -0pi`, temp-file rewrite + `mv`, `cp`/`install` replacements), and simple inline Python rewrite/write patterns. JSON output includes `oracle_targets`, `oracle_loc_non_boilerplate`, `touched_roots`, and `frontier_concentration`.

### Standalone instruction audit

```bash
# Run just the RC6 instruction-specificity check without the oracle-parsing
# overhead. Useful during instruction iteration.
python3 instruction_audit.py tasks/<task-name>
python3 instruction_audit.py tasks/<task-name> --json
```

Exit codes match `collapse_check.py` (0/1/2). The JSON output includes the raw signal families so you can see exactly which algorithms, CLI flags, schema clusters, or scope closures triggered the classification.

## Validation Loop (Step 2a)

```bash
# Initialize a new validation loop
python validate_loop.py init <task-name>

# Record attempt results with structured evidence
# The loop first validates the evidence against specs/validation_schema.json,
# then derives the score from the semantically validated evidence. GO is blocked
# if schema validation fails, required fields are missing, or blocking checks fail.
python validate_loop.py record <task-name> --evidence /tmp/<task-name>-validation-evidence.json

# Save BOTH files after record:
# - SAVE_TO => authoring spec path
# - REVIEWER_SAVE_TO => reviewer appendix path
#
# Select winner from candidates (after plateau). The CANDIDATES line is emitted
# as attempt=authoring-path|reviewer-path entries, and --winner accepts the
# attempt number, the authoring path, or the reviewer path.
python validate_loop.py select <task-name> --winner N
python validate_loop.py select <task-name> --winner specs/<task-name>-candidate-1.md
python validate_loop.py select <task-name> --winner specs/<task-name>-candidate-1-reviewer.md

# Check current state
python validate_loop.py status <task-name>

# Reset and start over
python validate_loop.py reset <task-name>
```

## Git Workflow

```bash
# Branch for new task
git checkout -b task/<task-name>

# Add and commit
git add tasks/<task-name>/
git commit -m "Add <task-name>: brief description"
git push origin task/<task-name>
```

## Packaging

```bash
# Create submission zip (files at archive root, no wrapping folder)
cd tasks/<task-name>
rm -f ../../Task_Ready_To_Submit/<task-name>.zip
zip -rq ../../Task_Ready_To_Submit/<task-name>.zip . -x '*/__pycache__/*' '*.pyc' '.*'

# Verify structure and required archive-root entries
python3 ../../validate_submission_zip.py ../../Task_Ready_To_Submit/<task-name>.zip
```

Verify: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/`, `solution/`, and `tests/` at archive root.

## Docker Troubleshooting

```bash
# Start Docker daemon (Cloud VM)
sudo dockerd &>/dev/null &
sleep 3
sudo chmod 666 /var/run/docker.sock

# Check Docker is running
docker ps

# Remove Harbor cgroup v2 resource limits (Cloud VM fix)
HARBOR_COMPOSE="$(python3 -c "import harbor; import pathlib; print(pathlib.Path(harbor.__file__).parent / 'environments/docker/docker-compose-base.yaml')")"
python3 -c "
import yaml
with open('$HARBOR_COMPOSE') as f:
    data = yaml.safe_load(f)
data['services']['main'].pop('deploy', None)
with open('$HARBOR_COMPOSE', 'w') as f:
    yaml.dump(data, f, default_flow_style=False)
"
```

## Frontier Models (Platform)

| Model | Provider string |
|---|---|
| GPT-5.2 | `openai/gpt-5.2` |
| Claude Opus 4.6 | `anthropic/claude-opus-4-6` |
| Claude Sonnet 4.6 | `anthropic/claude-sonnet-4-6` |

The repo-local quality check uses `openai/gpt-5.2`. Platform-side difficulty evaluation is run by the platform after upload and is not part of this repo's approval gate.
