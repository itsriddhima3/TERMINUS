# AGENTS.md

## Cursor-specific instructions

This is a **Terminal-Bench 3.0 Edition 2** benchmark task collection repository. There is no single application — the repo contains independent benchmark tasks, each with its own Docker-based environment, tested via the `harbor` CLI.

### Required tools

- **uv** — Python package manager (`uv tool install harbor`)
- **harbor** — CLI for initializing, building, testing, and running tasks
- **Docker** — Each task runs inside a Docker container

### Source of truth

All behavioral rules live in `.cursor/rules/`. Do not restate rules from those files here — reference them.

| File | Purpose | Auto-applied? |
|---|---|---|
| `.cursor/rules/task-creation.mdc` | File layout, metadata, templates (standard + UI), Dockerfile, tests, oracle, packaging | Yes |
| `.cursor/rules/review-and-submit.mdc` | Review checklist, decision criteria, blocking conditions, static checks | Yes |
| `.cursor/rules/difficulty-calibration.mdc` | Collapse audit (too easy), per-test feasibility (too hard), verifier health | Yes |
| `.cursor/rules/idea-validation.mdc` | Anti-trivialization checks, rubric axes, spec format. Reference with `@idea-validation.mdc` | No |

### Other references

| File | Purpose |
|---|---|
| `commands.md` | All harbor, CI, collapse-check, validation-loop, git, and debug commands |
| `workflow-prompts.md` | Ready-to-paste prompts for each workflow step (Steps 1 → 2a → 2b → 3a → 3b) |
| `Task_Ready_To_Submit/REFERENCE.md` | **Reference (golden) task catalog.** Five worked-out hard tasks across debugging / scientific-computing / software-engineering / build-and-dependency-management / games. Read the catalog and the matching `.zip` before authoring a similar task. The shipping zips, not the regression-fixture copies, are the authoritative reference. |
| `specs/validation_schema.json` | Required JSON contract for Step 2a validation evidence |
| `collapse_check.py` | Mechanical collapse/discoverability checker — RC1-RC7, including the instruction-specificity and oracle-triviality gates |
| `instruction_audit.py` | Mechanical spec-completeness audit of `instruction.md` (powers RC6). Runnable standalone. |
| `validate_loop.py` | Validation loop state machine for Step 2a (tracks attempts, early stopping, candidate selection) |
| `CNI.md` | Currently Not Implementing — ideas deliberately on the back burner, with the reason why. Read before proposing any of: platform-agnostic hard-task pattern library, instruction-diversity repo-wide lint, per-model calibration heuristics, static oracle-tests parity check. |
| `REPO_CONVENTIONS.md` | Documents intentional repo-specific conventions that external reviewers recurrently flag as "non-standard" (e.g., `output_contract.toml` at task root, `test.sh` without `set -euo pipefail`, varied instruction prose density). Link reviewers here instead of "fixing" the task in ways that would contradict `.cursor/rules/`. |

### Key principles

- **Rules in `.cursor/rules/` are authoritative.** When creating new tasks, follow those rules, not patterns from existing tasks in `tasks/`.
- **`tasks/` is the active authoring workspace.** Checked-in tooling/regression fixtures live under `repo_tests/fixtures/tasks/` so contributors do not learn from negative examples.
- **The default Edition 2 authoring/review path is hard-only.** If the repo ever adds another acceptance profile, it must be named explicitly instead of implied by mixed docs.
- **`task-creation.mdc` covers both standard and UI tasks.** Check it for the correct test.sh template, oracle structure, and verifier requirements for your task type.
- **`commands.md` is the canonical CLI reference.** Do not rely on command syntax from other documents.

### Specs folder

Step 2a saves validated specs to `specs/<task-name>.md`. The validation loop is managed by `validate_loop.py`. The `specs/` folder is a working directory — its contents are not submitted.

### Cloud VM Docker gotcha

In the Cursor Cloud VM (Docker-in-Docker inside Firecracker), containers fail to start with cgroup v2 errors if Docker Compose applies resource limits. See `commands.md` § Docker Troubleshooting for the fix.
