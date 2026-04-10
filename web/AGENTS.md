# AGENTS.md

## Standalone Bundle Purpose

This folder is a standalone attachment bundle for website LLM chats used to generate, evaluate, and draft Terminal-Bench 3 / Terminus Edition 2 tasks.

Treat the bundle as self-contained:

- do not ask for repo rule files or repo documentation unless the user explicitly wants repo-local validation after drafting
- keep references inside this bundle limited to sibling files in `web/` plus the companion kickoff prompt `chatgpt-task-kickoff-template.md`
- use repo paths like `tasks/<task-name>/...` only when describing the task files being drafted

## Precedence

- If two bundle files differ on an explicit authoring rule, follow `terminal-bench-task-creation.md`.
- If the question is about static checks, packaging, or submission-readiness, follow `static-checks-checklist.md`.
- If the question is about whether a task idea is strong enough to pursue, follow `TASK_PROPOSAL_RUBRIC.md`.
- This bundle is synced to the current active authoring rules.
- If the active rules are silent or ambiguous on a point, prefer the stricter interpretation already stated elsewhere in this bundle. If the bundle still does not resolve it, call out the ambiguity instead of inventing a new rule.
- One intentional bundle-specific override remains: during early ideation and first-pass drafting, default difficulty to `hard` unless the user explicitly asks for a different label. That is a drafting convenience, not a claim that the final task has already earned `hard` empirically.

## Bundle Files

- `chatgpt-task-authoring-playbook.md`
  Use for the full website-LLM workflow: intake, idea screening, anti-trivialization checks, proposal shaping, drafting, and self-audit.

- `terminal-bench-task-creation.md`
  Use for the canonical file layout, metadata rules, milestone structure, verifier design, rubric workflow, and validation commands.

- `static-checks-checklist.md`
  Use when judging whether a draft is compliant, ready for local validation, or close to submission-ready.

- `TASK_PROPOSAL_RUBRIC.md`
  Use when screening an idea before drafting files or when deciding whether to continue, regenerate, or stop.

- `chatgpt-task-kickoff-template.md`
  Use as the initial prompt pasted into a website LLM together with the bundle.

## Intent Routing

1. If the user wants idea generation, first-pass drafting, or screenshot-based intake:
   use `chatgpt-task-authoring-playbook.md` and the kickoff template.

2. If the user wants a rules answer about task files, metadata, verifier structure, milestones, Dockerfiles, or task quality:
   use `terminal-bench-task-creation.md`.

3. If the user wants a go/no-go judgment on whether an idea should be pursued:
   use `TASK_PROPOSAL_RUBRIC.md`.

4. If the user wants to know whether a draft is compliant, ready for repo-local validation, or ready to package:
   use `static-checks-checklist.md`.

## Shared Defaults

- `author_name = "anonymous"`
- `author_email = "anonymous"`
- use `subcategories`, never `task_subtypes`
- prefer single-container tasks unless the task genuinely needs compose or multiple services
- prefer non-milestone tasks unless the user explicitly requests milestones or the source screenshot clearly includes them
- confirm UI-task status and docker-compose need only when the task idea actually suggests them
- default difficulty to `hard` during ideation in this standalone bundle; validate that label later with real runs before treating it as final

## Early Ideation Guardrails

- avoid Python unless there is a compelling reason to choose it over other languages
- avoid FastAPI unless there is a compelling reason to choose it
- `long_context` is only valid when the task truly needs at least 50k tokens of reading, roughly 50-150 pages, and semantic reasoning rather than simple parsing or keyword search
- `api_integration` is only valid when the API is mocked locally in Docker with no external web access
- UI tasks should be treated as Playwright-tested UI work using the UI verifier stack, not as ordinary pytest-only backend tasks

## What This Bundle Must Not Do

- Do not send the model back to repo docs just to recover rules already summarized here.
- Do not preserve stale legacy file names or rule wording.
- Do not treat the bundle's `hard` default as permission to skip later empirical validation.
- Do not claim a task is ready to submit, CI-clean, or benchmark-valid unless the real local checks were actually run in the repo environment.
