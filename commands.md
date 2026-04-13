# Commands Reference

All harbor, CI, validation, and debug commands for Terminal-Bench 3 task development.

## Harbor — Task Validation

```bash
# Source API key first (required for agent trials and quality checks)
set -a && source .env && set +a

# Oracle (must score 1.0) — run 3x to catch flakiness
harbor run -p "tasks/<task-name>" -a oracle

# NOP (must score 0.0)
harbor run -p "tasks/<task-name>" -a nop

# Agent trial — Anthropic (1 min, 3 preferred, 5 max — want pass rate <20% for hard tasks)
harbor run -p "tasks/<task-name>" -a terminus-2 -m "anthropic/claude-opus-4-6"

# Quality check
harbor tasks check "tasks/<task-name>" -m "anthropic/claude-sonnet-4-6"

# Interactive debug (shell into the container)
harbor tasks start-env -p "tasks/<task-name>" -e docker -a -i

# Init new task skeleton
harbor tasks init <task-name> --include-standard-metadata --tasks-dir tasks/
```

### Interpreting results

- **Mean 1.0** = agent passed all tests (bad for hard tasks — too easy)
- **Mean 0.0** = agent failed all tests (good for hard tasks, expected for NOP)
- **Errors** = agent crashed before producing a result (infra issue, not task issue)
- **Target for hard tasks:** agent pass rate <20% across 3-5 trials
- **Too easy:** pass rate > 80% → task needs hardening or redesign
- **Too hard:** any individual test that is 0/N across all trials → that test needs fixing

### Local vs platform difficulty

Local trials with one model (e.g., Claude Opus 4.6) are a **lower-confidence proxy**, not the platform's actual difficulty decision. The platform runs 10 trials across 2 frontier models (Claude Opus 4.6 + GPT-5.2) and uses the better-performing model's score. A task that passes 0/5 locally with Claude might still pass 3/10 with GPT-5.2 on the platform (or vice versa). Treat local results as a signal, not a guarantee.

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
# Edition 2 static checker (PREFERRED — task-scoped, runs all checks)
python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2

# Individual checks (these scan ALL tasks by default — pass task dir when supported)
bash ci_checks/check-no-canary.sh tasks/<task-name>
bash ci_checks/check-dockerfile-sanity.sh tasks/<task-name>
bash ci_checks/check-test-sh-sanity.sh tasks/<task-name>
bash ci_checks/validate-task-fields.sh tasks/<task-name>

# NOTE: Some ci_checks/*.sh scripts don't accept a task path and scan the entire
# tasks/ directory. This means legacy tasks may cause spurious failures.
# Always use run_static_checks.py --task-dir for reliable per-task checking.

# Lint test file
ruff check tasks/<task-name>/tests/
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

# Verify structure
unzip -l ../../Task_Ready_To_Submit/<task-name>.zip
```

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
