# AGENTS.md

## Cursor Cloud specific instructions

This is a **Terminal-Bench 3.0** benchmark task collection repository. There is no single application to build/run — the repo contains independent benchmark tasks, each with its own Docker-based environment, tested via the `harbor` CLI.

### Required tools

- **uv** — Python package manager, used to install Harbor
- **harbor** — CLI framework for initializing, building, testing, and running benchmark tasks (`uv tool install harbor`)
- **Docker** — Each task runs inside a Docker container

### Key commands (see CONTRIBUTING.md for full details)

| Action | Command |
|---|---|
| Run oracle (must score 1.0) | `harbor run -p "tasks/<name>" -a oracle` |
| Run nop (must score 0.0) | `harbor run -p "tasks/<name>" --agent nop` |
| Interactive debug | `harbor tasks start-env -p "tasks/<name>" -e docker -a -i` |
| Init new task | `harbor tasks init <name> --include-canary-strings --include-standard-metadata --tasks-dir tasks/` |

### CI / lint checks

The `ci_checks/` directory contains shell scripts that validate task structure. They are designed to run on PR diffs but also work standalone:

```
bash ci_checks/check-no-canary.sh               # all tasks (optional: tasks/<name> or file paths)
bash ci_checks/check-dockerfile-sanity.sh       # all Dockerfiles
bash ci_checks/check-test-sh-sanity.sh          # all test.sh files
bash ci_checks/validate-task-fields.sh           # all task.toml fields
bash ci_checks/check-test-file-references.sh     # test file references
bash ci_checks/check-dockerfile-references.sh    # Dockerfile references
bash ci_checks/check-task-absolute-path.sh       # absolute path usage
```

**Envgen / submission pipeline:** put `author_name`, `author_email`, and other Edition 2 metadata under a **`[metadata]`** table in `task.toml` (not only at top level). Run `python3 run_static_checks.py --task-dir tasks/<name> --version edition_2` before claiming a task is submission-ready (see `.cursor/rules/static-checks-checklist.mdc`).

**Python verifiers:** `tests/test.sh` should run `tests/test_outputs.py` with **pytest** under **uv** (see `.cursor/rules/terminal-bench-task-creation.mdc`), not `python3 /tests/test_outputs.py` or a custom test driver.

### Cloud VM Docker gotcha

In the Cursor Cloud VM (Docker-in-Docker inside Firecracker), containers fail to start with cgroup v2 errors if Docker Compose applies resource limits. After installing Harbor, you must remove the `deploy` section from Harbor's compose base file:

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
