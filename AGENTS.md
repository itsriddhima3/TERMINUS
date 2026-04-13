# AGENTS.md

## Cursor-specific instructions

This is a **Terminal-Bench 3.0 Edition 2** benchmark task collection repository. There is no single application — the repo contains independent benchmark tasks, each with its own Docker-based environment, tested via the `harbor` CLI.

### Required tools

- **uv** — Python package manager (`uv tool install harbor`)
- **harbor** — CLI for initializing, building, testing, and running tasks
- **Docker** — Each task runs inside a Docker container

### Rule files

Three cursor rules auto-apply to every conversation:

| File | Purpose |
|---|---|
| `.cursor/rules/task-creation.mdc` | File layout, metadata, instruction styling, Dockerfile, tests, oracle, packaging |
| `.cursor/rules/review-and-submit.mdc` | Review checklist, static checks, common issues, submission readiness |
| `.cursor/rules/difficulty-calibration.mdc` | Collapse audit (too easy), per-test feasibility (too hard), multi-trial gate |

Additional references (NOT auto-applied — use `@filename` to reference):

| File | Purpose |
|---|---|
| `.cursor/rules/idea-validation.mdc` | Anti-trivialization checks, rubric axes, accept/reject exemplars, spec output format. Used in Step 2. |
| `commands.md` | All harbor, CI, git, and debug commands in one place |
| `workflow-prompts.md` | Ready-to-paste prompts for each workflow step (ChatGPT ideation → Cursor validate+spec → Cursor create → Cursor review) |

### Existing tasks

The `tasks/` directory contains Edition 2 tasks. When creating new tasks, always follow the rules in `.cursor/rules/` — they are the source of truth, not patterns from existing tasks.

### Specs folder

Step 2a saves validated specs to `specs/<task-name>.md`. The validation loop is managed by `validate_loop.py` — a Python script that tracks attempts, handles early stopping, and manages candidate files. The `specs/` folder is a working directory — its contents are not submitted.

### Python verifiers

`tests/test.sh` must run `tests/test_outputs.py` with **pytest** under **uv** (see `task-creation.mdc`). Never use `python3 /tests/test_outputs.py` or a custom test driver.

### Envgen / submission pipeline

Put all Edition 2 metadata under a `[metadata]` table in `task.toml`. Run `python3 run_static_checks.py --task-dir tasks/<n> --version edition_2` before claiming submission-ready.

### Cloud VM Docker gotcha

In the Cursor Cloud VM (Docker-in-Docker inside Firecracker), containers fail to start with cgroup v2 errors if Docker Compose applies resource limits. After installing Harbor, remove the `deploy` section from Harbor's compose base file:

```bash
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

Also ensure Docker daemon is started with fuse-overlayfs storage driver, iptables-legacy, and the socket is readable:

```bash
sudo dockerd &>/dev/null &
sleep 3
sudo chmod 666 /var/run/docker.sock
```
