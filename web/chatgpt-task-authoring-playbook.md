# Website LLM Task Authoring Playbook

Use this playbook when you want a website LLM chat to help you design or draft a Terminal-Bench 3 / Terminus Edition 2 task from attachments.

This file is written to work for ChatGPT, Gemini, and similar attachment-based web chats.

## Attachment Workflow

Attach the standalone bundle, not repo rule files:

- `AGENTS.md`
- `chatgpt-task-authoring-playbook.md`
- `terminal-bench-task-creation.md`
- `static-checks-checklist.md`
- `TASK_PROPOSAL_RUBRIC.md`
- `chatgpt-task-kickoff-template.md`

Optional extra attachments:

- a task-card screenshot
- a short typed fallback idea
- one rough note about the real-world problem you want the task to model

Treat the attached standalone bundle as authoritative. Do not ask for repo rule files or repo documentation unless the user explicitly asks for repo-local validation later.

## Best Website Workflow

- use the strongest reasoning mode available
- keep the chat in phases rather than jumping straight to files
- use regeneration internally; only surface the strongest surviving candidate
- do not claim a task is ready to submit or CI-clean unless someone actually ran the real repo-local checks afterward

## Bundle Defaults

Use these fixed values unless the user explicitly overrides them:

- `author_name = "anonymous"`
- `author_email = "anonymous"`
- `version = "2.0"`
- standalone drafting default: `difficulty = "hard"`

Important:

- the `hard` default is a bundle-level ideation preference, not proof that the finished task empirically qualifies as hard
- use `subcategories` only
- do not use `task_subtypes`
- avoid choosing Python as the default implementation language unless the idea clearly calls for it
- avoid choosing FastAPI as the default framework unless there is a strong justification
- prefer single-container unless the task clearly needs docker-compose / multiple services
- default to a non-milestone task unless the screenshot or user explicitly calls for milestones

## Phase 0: Intake

Before drafting files, gather only the minimum input that truly must come from the user.

Required source input:

1. either an attached task-card screenshot
2. or a typed task idea

If both are missing, ask only for one of them and stop.

### What to infer instead of asking

Infer these when the idea is clear enough:

- primary language(s)
- category
- subcategories
- whether the task should be milestone-based
- whether it is truly a UI task
- whether it truly needs docker-compose / multiple services
- short human-facing title
- short kebab-case task slug

### Screenshot precedence

If a screenshot is attached:

- use it as the primary source
- extract the displayed task title, short description, language chips, category labels, subtype-like labels, and visible milestones
- normalize display labels to accepted metadata values before drafting

If no screenshot is attached:

- use the typed task idea as the primary source

### Metadata normalization

Normalize human-facing labels into accepted task metadata values:

- `API Integration` -> `api_integration`
- `DB Interaction` -> `db_interaction`
- `Long Context` -> `long_context`
- `Tool Specific` -> `tool_specific`
- `UI Building` -> `ui_building`

If none apply, use:

```toml
subcategories = []
```

Subtype guardrails:

- use `long_context` only when the source idea clearly implies at least 50k tokens of reading, roughly 50-150 pages, and semantic reasoning rather than simple parsing/search
- use `api_integration` only when the API is local and mockable inside Docker with no external web access
- use `ui_building` only when the task is genuinely UI-facing and intended for the UI verifier stack / Playwright-style testing path
- do not default to Python as the implementation language if another language fits the task naturally
- do not default to FastAPI just because the task mentions an API

### Title and slug rules

- keep the title to 3-4 words max
- keep it compact and task-card friendly
- avoid stack dumps in the title
- keep framework details in the description, tags, languages, and metadata
- derive the slug from the same short final title
- do not turn the whole task description into the slug

Examples:

- bad title: `Harden Flask React JWT Auth App Against Account Takeover`
- better title: `JWT Takeover Defense`
- bad slug: `harden-flask-react-jwt-auth-app-against-account-takeover`
- better slug: `jwt-takeover-defense`

### Milestone rules

If milestones are required:

- use `milestone_1.md ... milestone_N.md`
- use `solve1.sh ... solveN.sh`
- use `test_m1.py ... test_mN.py`
- `instruction.md` must still contain the overall intro plus every milestone description

## Phase 1: Proposal Screen

Evaluate the idea against the six rubric axes:

- verifiable
- well-specified
- solvable
- difficult for a good reason
- realistic or valuable
- outcome-verified

Reject or warn on ideas that are:

- mostly busywork
- giant in implementation scope
- hard mainly because of hidden-instance discovery
- subjective to grade
- easy once the checked behavior is stated honestly
- too close to generic class projects
- unjustifiably Python-first
- unjustifiably FastAPI-first

### Anti-trivialization checks

Run these before allowing the idea to proceed:

1. **Disclosure-collapse test**
   If the task becomes easy once the checked behavior is stated honestly in `instruction.md`, redesign or reject it.

2. **Hidden-instance test**
   If the task is hard mainly because the agent does not know which one file, one day, one record, or one artifact is broken, redesign or reject it.

3. **Single-artifact repair test**
   If the likely solution is just "patch one manifest" or "restore one report" without a broader implementation fix, redesign or reject it.

4. **Generalization test**
   Ask whether the same implementation should work across multiple workloads, seeds, or scenario families.

5. **Prompt-honesty test**
   If an honest prompt would need to reveal the exact broken instance or gold output and that would collapse the search space, redesign or reject it.

6. **Cheating-vs-difficulty test**
   Preventing cheating is necessary, but anti-cheating measures do not create legitimate difficulty by themselves.

7. **Mechanical-fix filter**
   Do not confuse verifier setup, reward footer, timeout tuning, or dependency placement with true task weakness.

8. **Localized-fix test**
   If the likely fix lives in one tiny function or one obvious conditional and the prompt already names the behavior precisely, treat that as a warning sign.

9. **Oracle-locality test**
   If the likely oracle mostly replaces one or two files wholesale, treat that as evidence the task may be too localized or too answer-revealing.

### Strong warning signs

- one hidden broken instance drives most of the difficulty
- the task becomes easy once exact checked behavior is disclosed
- the likely oracle is a tiny patch rather than a real systems or source-level fix
- the likely patch surface is one tiny obvious helper
- fake `long_context` where the material is below the real threshold or solvable by simple parsing/search
- remote or non-local API dependency under `api_integration`
- UI task framed like a backend pytest task instead of real UI work
- Python chosen by default without a good reason
- FastAPI chosen by habit rather than because it materially fits the task

### Signals that the idea is still strong

- the prompt can be honest about checked behavior and the task is still hard
- the verifier exercises multiple legitimate and adversarial scenarios
- the likely fix changes real behavior rather than repairing one artifact
- remaining issues are mostly mechanical or compliance-level

If the current candidate is weak, regenerate internally and carry forward only the strongest surviving variant.

## Phase 2: Implementation Spec

Before generating files, produce:

1. a one-paragraph task summary
2. the extracted source fields from the screenshot or typed fallback
3. the extracted milestones, or `no milestones provided`
4. the chosen or normalized language(s), category, subcategories, final short title, final slug, and whether the task is milestone-based
   If Python or FastAPI is used, explicitly state why that choice is justified.
   If `long_context`, `api_integration`, or `ui_building` is used, explicitly state why the task qualifies for that subtype.
5. the anti-trivialization verdict, including the localized-fix and oracle-locality tests
6. the exact file tree
7. the agent-visible outputs the verifier will check
8. cheating risks and how the verifier avoids answer leakage
9. why the task is hard for a good reason

Do not draft files if the anti-trivialization verdict is weak.

## Phase 3: Draft the Task

Generate the task for the strongest surviving candidate from the latest ideation pass, whether it was original or regenerated.

### Minimum files for a standard non-milestone task

- `tasks/<task-slug>/instruction.md`
- `tasks/<task-slug>/task.toml`
- `tasks/<task-slug>/environment/Dockerfile`
- `tasks/<task-slug>/solution/solve.sh`
- `tasks/<task-slug>/tests/test.sh`
- `tasks/<task-slug>/tests/test_outputs.py`

### Minimum files for a milestone task

- `tasks/<task-slug>/instruction.md`
- `tasks/<task-slug>/task.toml`
- `tasks/<task-slug>/milestone_1.md`
- `tasks/<task-slug>/milestone_2.md`
- `tasks/<task-slug>/... milestone_N.md`
- `tasks/<task-slug>/environment/Dockerfile`
- `tasks/<task-slug>/solution/solve.sh`
- `tasks/<task-slug>/solution/solve1.sh`
- `tasks/<task-slug>/solution/solve2.sh`
- `tasks/<task-slug>/solution/... solveN.sh`
- `tasks/<task-slug>/tests/test.sh`
- `tasks/<task-slug>/tests/test_m1.py`
- `tasks/<task-slug>/tests/test_m2.py`
- `tasks/<task-slug>/tests/... test_mN.py`

If the task is a true UI task, include the maintained UI verifier stack instead of inventing ad hoc UI checks.

## Bundle Hard Rules

### `instruction.md`

- keep it concise, natural, and human-written
- use absolute paths only
- list every output file the verifier inspects
- if output is structured, define the schema directly
- if the verifier depends on exact object/dict key formats, define those too
- do not include hints, solution steps, or hidden verifier logic
- do not include canary strings
- do not include the task name

### `task.toml`

- keep metadata under `[metadata]`
- include `difficulty`, `category`, `tags`, `languages`, `codebase_size`, `number_of_milestones`, and `subcategories`
- keep `tags` to 3-6 descriptive values
- use `subcategories = []` unless an accepted value really applies
- do not use `task_subtypes`
- do not include `task_id`
- if `environment/docker-compose.yaml` is used, set `custom_docker_compose = true`
- if multiple services are used, also set `is_multi_container = true`

### `environment/Dockerfile`

- pin every `FROM` stage by digest
- leave apt packages unversioned in this repo
- keep verifier-only dependencies out of the image
- put runtime dependencies in the image
- set `WORKDIR` explicitly
- do not copy `solution/` or `tests/` into the image

### `tests/test_outputs.py`

- use the exact file name `test_outputs.py`
- write normal pytest tests
- add informative docstrings
- cover every explicit requirement or prohibition in `instruction.md`
- verify outcomes, not hidden implementation details
- avoid answer leakage and wall-clock assertions

### Milestone verifiers

- use `test_m1.py ... test_mN.py`
- each milestone test should score only its own milestone
- run milestone Python verifiers through pytest from `tests/test.sh`

### `tests/test.sh`

- use `set -euo pipefail`
- initialize the reward file early
- keep verifier dependencies and verifier-only runtimes in `tests/test.sh`
- run Python verifiers through `uvx` or `uv run pytest`, not plain `python3`
- end with the exact literal reward footer

## Required Output Format From the Website LLM

When drafting, respond in this order:

1. `Decision`
   Use exactly one of: `GO`, `REGENERATE`, `STOP`
2. `Why in 3 bullets max`
   The first bullet must say whether the chosen candidate is original or regenerated
3. `Chosen metadata`
4. `Anti-trivialization verdict`
5. `Implementation plan`
6. `File tree`
7. one fenced code block per file, labeled with its repo path
8. `Self-audit`

If regeneration happens internally and a regenerated variant is the strongest viable candidate, the final decision should still be `GO`, not `REGENERATE`.

## Self-audit Requirements

The self-audit must explicitly confirm:

- whether the screenshot or typed fallback was the primary source
- chosen language(s), category, subcategories, extracted milestones if any, generated title, and derived slug
- the title is short and derived from the final chosen idea
- `subcategories` uses only accepted lowercase values
- `task_subtypes` is not used
- `tags` stays within the 3-6 range
- the task does not rely on one hidden broken instance or one hidden expected payload
- the task would still be hard if the prompt honestly stated the checked behavior
- any remaining likely fixes are concept-level or mechanical/compliance-level
- the likely patch surface is not so localized that the answer is obvious from the statement
- absolute paths are used in `instruction.md`
- structured outputs document exact key formats when tests depend on them
- `tests/test.sh` uses `set -euo pipefail`
- `instruction.md` is readable and not a dense wall of text
- Python verifiers use pytest via `uv`
- every explicit requirement/prohibition gets direct verifier coverage
- the exact reward footer is present
- milestone Python verifiers, if any, also use pytest
- every `FROM` stage is digest-pinned
- verifier-only dependencies stay in `tests/test.sh`
- the task is still a draft until real local checks run

## What the Website LLM Must Never Claim

Do not say the task is ready to submit, CI-clean, or benchmark-valid unless the real local commands were actually run afterward.

If no local execution happened, say explicitly:

- this is a draft
- oracle and nop still need to be run
- static checks still need to be run
