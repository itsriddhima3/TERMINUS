# Commands Reference

All harbor, CI, validation, and debug commands for Terminal-Bench 3 task development.

## Harbor — Task Validation

```bash
# Preflight: oracle and NOP may be launched in parallel in separate terminals
# as long as task files are not being edited during the run.
# Oracle stress test — 10 parallel runs (no API key needed)
harbor run -p "tasks/<task-name>" -a oracle -k 10

# NOP (must score 0.0, no API key needed)
harbor run -p "tasks/<task-name>" -a nop

# Only after BOTH oracle and NOP pass:
# Source API key (required for quality check and agent trials only)
set -a && source .env && set +a

# Quality check
harbor tasks check "tasks/<task-name>" -m "anthropic/claude-opus-4-6"

# Only after quality check passes or HIGH findings are repaired:
# Agent trials — 5 parallel Claude Opus 4.6 runs (default hard-task gate, requires API key)
harbor run -p "tasks/<task-name>" -a terminus-2 -m "anthropic/claude-opus-4-6" -k 5

# Interactive debug (shell into the container)
harbor tasks start-env -p "tasks/<task-name>" -e docker -a -i

# Init new task skeleton
harbor tasks init <task-name> --include-standard-metadata --tasks-dir tasks/
```

### Parallel execution notes

- `-k N` runs N trials concurrently with isolated job directories — use this instead of running commands sequentially
- Oracle: use `-k 10` (10 parallel runs) to catch flakiness efficiently
- Agent trials: use `-k 5` for 5 concurrent trials per model
- Each parallel run gets its own job directory, results are aggregated automatically
- `oracle -k 10` and `nop` are safe to run at the same time as preflight in separate terminals
- Do not start quality check or agent trials until both preflight runs have passed
- Do not overlap `verifier_health.py` with real Step 3a harbor runs on the same task directory; it launches additional oracle jobs and temporary task copies for randomized-order and partial-oracle checks

### Interpreting results

- **Mean 1.0** = agent passed all tests (bad for hard tasks — too easy)
- **Mean 0.0** = agent failed all tests (good for hard tasks, expected for NOP)
- **Errors** = agent crashed before producing a result (infra issue, not task issue)
- **Target for the default hard-only Edition 2 path:** agent pass rate <20% across 5 `anthropic/claude-opus-4-6` trials by default
- **With the default 5-trial gate:** only `0/5` qualifies as hard; `1/5 = 20%` is medium/borderline and is not approvable
- **Medium range:** pass rate 20-80% means the task is not approvable on the default hard-only path
- **Too easy:** pass rate > 80% → task needs hardening or redesign
- **Too hard:** any individual test that is 0/N across all trials → that test needs fixing

### Local vs platform difficulty

Local trials with one model are a **lower-confidence proxy**, not the platform's actual difficulty decision. The platform runs 10 trials across 2 frontier models (5 Claude Opus 4.6 + 5 GPT-5.2) and uses the better-performing model's score.

The current repo archive has no GPT-5.2 job artifacts, so repo reviews default to the 5-trial Claude Opus 4.6 gate. Treat missing GPT-5.2 evidence conservatively:
- `0/5` on Claude clears the repo's default hard gate, but GPT-5.2 may still score higher on the platform.
- `1/5 = 20%` or any higher Claude pass rate is already non-approvable on the repo's hard-only path. Missing GPT-5.2 evidence cannot rescue a borderline Claude result because the platform uses the better-performing model.
- If GPT-5.2 artifacts become available, recompute difficulty using the higher pass rate between the two models.

### Extracting per-test pass matrix from trial logs

Harbor stores job artifacts in this shape:

```text
<job-dir>/result.json
<job-dir>/<trial-name>/result.json
<job-dir>/<trial-name>/verifier/ctrf.json
```

After agent trials, analyze the exact job directory Harbor printed:

```bash
# Human-readable summary: mean reward, full-suite pass rate, per-trial rewards,
# per-test pass matrix, and infra errors.
python3 analyze_trials.py <job-dir>

# Optional machine-readable form.
python3 analyze_trials.py <job-dir> --json
```

Do NOT use a broad `find jobs/` across old runs. Any test that is 0/N across the verifier-backed trials should be investigated — it may be too hard or broken.

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
# NOTE: run_static_checks.py does NOT run collapse_check.py, Harbor quality checks,
# or agent-trial analysis, and it does not determine approval on its own.
# It covers the repo-local static rule set only.

# Lint test file
ruff check tasks/<task-name>/tests/
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

```bash
# Single repo gate for the default hard-only Edition 2 path.
# Use the exact job directory printed by Harbor for the 5-trial Claude run.
# Pass the verifier-health JSON emitted above.
python3 approve_task.py --task-dir tasks/<task-name> --zip Task_Ready_To_Submit/<task-name>.zip --job-dir jobs/<job-dir> --verifier-health /tmp/<task-name>-verifier-health.json

# Optional machine-readable form.
python3 approve_task.py --task-dir tasks/<task-name> --zip Task_Ready_To_Submit/<task-name>.zip --job-dir jobs/<job-dir> --verifier-health /tmp/<task-name>-verifier-health.json --json
```

`approve_task.py` is the authoritative repo-local hard-task approval gate. It consumes the saved `verifier_health.py` report and bundles `run_static_checks.py`, `collapse_check.py`, `validate_submission_zip.py`, `analyze_trials.py`, manifest verification, and zip/source parity checks. Exit 0 is required before calling a hard task approved or ready in this repo.

## Repo Tooling Regressions

```bash
# Repo-level regression suite for run_static_checks.py, collapse_check.py,
# verifier_health.py, analyze_trials.py, and approve_task.py against the
# checked-in task and synthetic fixtures.
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

Checks: oracle simplification, oracle predictability, verifier shallowness, tamper surface, and agent-visible reference artifacts on the solver-visible file surfaces from `@task-creation.mdc` (`instruction.md`, `tests/`, and `environment/`; excluding `task.toml` and `output_contract.toml`).

The oracle/frontier checks are transitive: `collapse_check.py` follows `solution/solve.sh`, solution-local called scripts, `patch -p1 < file.patch`, heredoc writes, in-place shell rewrites (`sed -i`, `perl -0pi`, temp-file rewrite + `mv`, `cp`/`install` replacements), and simple inline Python rewrite/write patterns. JSON output includes `oracle_targets`, `oracle_loc_non_boilerplate`, `touched_roots`, and `frontier_concentration`.

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

Difficulty is based on the **better-performing model's** pass rate across 10 trials (5 per model).
