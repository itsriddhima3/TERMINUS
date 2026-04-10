# Website LLM Task Kickoff Template

Paste this into a website LLM chat together with the standalone attachment bundle.

Attach:

- `AGENTS.md`
- `chatgpt-task-authoring-playbook.md`
- `terminal-bench-task-creation.md`
- `static-checks-checklist.md`
- `TASK_PROPOSAL_RUBRIC.md`

### Idea generation pass

```text
Before Phase 0, do an idea-generation pass only.

Generate 8-12 candidate Terminal-Bench 3 task ideas in this domain:
[fill in the domain]

Requirements:
- keep only hard tasks that are difficult for a good reason
- reject class-project ideas, giant scopes, busywork, subjective grading, and hidden-instance gimmicks
- apply the rubric and anti-trivialization checks before showing me anything
- if the first batch is weak, regenerate internally and present only the strongest surviving ideas
- show only the best 3-5 ideas at the end
- avoid using Python as the implementation language unless there is a compelling reason
- avoid using FastAPI unless there is a compelling reason
- do not label ideas as `long_context`, `api_integration`, or UI unless they actually satisfy the strict criteria

For each shown idea, give:
- short title
- 1-2 sentence concept
- why it is hard for a good reason
- what the verifier would check at a high level
- biggest likely rejection risk
- verdict: `strong candidate`, `borderline`, or `reject`

End by naming the single best idea to carry into Phase 0. Do not draft files yet.
```
### Phase 0 pass

```text
You are helping me design and draft a Terminal-Bench 3 / Terminus Edition 2 task.

Follow the attached standalone bundle exactly. The attached bundle is authoritative for this chat. Do not ask me to attach repo rule files or repo documentation unless I explicitly ask for repo-local validation later.

Important behavior:
- Work in phases.
- Do not jump into writing files if the source idea is missing.
- If a task-card screenshot is attached, use it as the primary source of truth.
- If both a screenshot and typed fallback text are present, prefer the screenshot unless it is unreadable or incomplete.
- If no screenshot is attached, use the typed fallback task idea.
- If the screenshot contains milestones, extract them and preserve that intent.
- Use milestone task structure only when milestones are visibly present or explicitly requested.
- For this standalone drafting workflow, use:
  - `author_name = "anonymous"`
  - `author_email = "anonymous"`
  - `version = "2.0"`
  - default `difficulty = "hard"` unless I explicitly override it
- Treat that `hard` default as a drafting preference, not as proof that the finished task already earned `hard` empirically.
- Decide primary language(s), category, subcategories, title, and slug yourself when the idea is clear enough.
- Avoid using Python as the implementation language unless there is a compelling reason.
- Avoid using FastAPI unless there is a compelling reason.
- Use `subcategories` only; do not use `task_subtypes`.
- Default to `subcategories = []` unless an accepted lowercase value applies.
- Accepted lowercase `subcategories` values are:
  - `long_context`
  - `tool_specific`
  - `api_integration`
  - `db_interaction`
  - `ui_building`
- Normalize human-facing labels like `API Integration` or `Long Context` into those accepted lowercase values.
- `long_context` only applies when the task truly requires at least 50k tokens of reading, roughly 50-150 pages, and semantic reasoning rather than simple parsing/search.
- `api_integration` only applies when the API is mocked locally in Docker with no external web access.
- UI tasks should use the UI verifier stack and Playwright-style testing rather than ordinary pytest-only validation.
- Generate a short human-facing title from the final selected best idea, then derive the kebab-case slug from that same short title.
- Keep the title to 3-4 words max.
- Avoid long stack-heavy names. Put framework details in the description, tags, languages, and metadata instead.
- Keep `instruction.md` natural and lightly formatted. Do not invent canned sections like `Deliverables`, `Artifacts`, or `Acceptance Criteria` unless the task genuinely needs them.
- If `instruction.md` describes a structured output artifact, specify exact object/dict key formats as well as value shapes whenever tests depend on them.
- For Python verifiers, run pytest under uv from `tests/test.sh`; do not use `python3 /tests/test_outputs.py` or custom `__main__` drivers.
- Use `set -euo pipefail` near the top of `tests/test.sh` unless there is a clearly justified exception.
- Keep verifier-only tools like `python3`, `uv`, `pytest`, `pytest-json-ctrf`, `openssh-client`, `ssh`, `sftp`, `curl`, and `jq` in `tests/test.sh` when the task itself does not need them.
- Keep base images digest-pinned and keep apt packages unversioned.
- Use current milestone file names if milestones are needed:
  - `milestone_1.md ... milestone_N.md`
  - `solve1.sh ... solveN.sh`
  - `test_m1.py ... test_mN.py`
- Make every explicit requirement or prohibition directly testable.
- Reject or redesign ideas that become easy once the prompt honestly states the checked behavior.
- Reject or redesign ideas that are only hard because one hidden file, day, manifest, or payload must be discovered.
- Prefer source-level or system-level fixes that generalize across multiple workloads or scenario families.
- If the only remaining issues are verifier setup, dependency placement, timeout tuning, reward-footer formatting, or similar compliance mechanics, treat those as mechanical fixes rather than core task weakness.
- Do not claim the task is ready to submit unless real local checks were actually run later in the repo environment.

When enough information is available:
1. Evaluate the task idea briefly against the rubric.
2. State whether you used the screenshot or typed fallback as the primary source.
3. State the extracted source fields.
4. State the extracted milestones if present, otherwise say `no milestones provided`.
5. State the chosen or normalized language(s), category, subcategories, generated short title, derived task slug, and whether this will be a milestone task.
   If Python or FastAPI was kept, state why that choice is justified.
   If `long_context`, `api_integration`, or `ui_building` was kept, state why the task really qualifies for that subtype.
6. Give an explicit anti-trivialization verdict. Include the disclosure-collapse, hidden-instance, single-artifact repair, generalization, mechanical-fix, localized-fix, and oracle-locality checks.
7. Start with a short decision card using exactly one of `GO`, `REGENERATE`, or `STOP`, followed by at most 3 short bullets.
8. In that decision card, identify whether the selected strongest candidate is original or regenerated.
9. Produce an implementation plan and file tree only if the final selected candidate is `GO`.
10. If regeneration happens internally, compare variants yourself and present only the strongest surviving candidate unless I explicitly ask for alternatives.
11. Draft the full task as separate file blocks with explicit repo paths only if the final selected candidate is `GO`.
12. Finish with a self-audit against the attached standalone bundle.

Here is my task brief:

Attached task-card screenshot:
[attach if available]

Fallback task idea:
[fill this in only if no screenshot is attached, or if you want backup text]

Extra context:
- optional language override: [optional]
- optional category override: [optional]
- optional subcategories override: [optional]
- optional task title override: [optional]
- optional milestone override: [optional]
- real-world motivation: [optional]
- expected outputs: [optional]
- environment notes: [optional]
- special constraints: [optional]
- similar existing tasks to avoid: [optional]

Start with Phase 0 only.
```

## Shorter Follow-up Prompts

Use these after the kickoff turn.



### Proposal pass (Phase 1-2)

```text
Move to Phase 1 and Phase 2 only. Do not draft files yet.

Start with a short decision card using exactly one of `GO`, `REGENERATE`, or `STOP`, followed by at most 3 short bullets. The first bullet must identify whether the selected candidate is original or regenerated.

Then give:
- task viability assessment
- whether you used the screenshot or typed fallback as the source
- extracted source fields
- extracted milestones if any
- chosen or normalized language(s), category, subcategories, generated title, derived slug, and whether this will be a milestone task
- the anti-trivialization verdict, including the localized-fix and oracle-locality tests
- verifier approach
- cheating-risk analysis
- exact file tree

If regeneration is needed, do it internally and present only the strongest surviving candidate.
```

### Full draft pass (Phase 3)

```text
The proposal looks good. Move to Phase 3 using the strongest selected candidate from the latest ideation pass, whether it was original or regenerated.

Draft all task files as separate fenced code blocks with explicit repo paths.

Finish with a self-audit that checks:
- `test_outputs.py` naming
- absolute paths
- no canned `Deliverables`/`Artifacts` instruction scaffolding
- no dense wall-of-text milestone instructions
- schema assertions for promised structured artifacts, including exact object/dict key formats when relevant
- `subcategories` using only accepted lowercase values and no `task_subtypes`
- `tags` staying within the 3-6 range
- every Docker `FROM` stage pinned by digest
- apt packages left unversioned
- Python verifiers using pytest via uv with no custom driver
- milestone verifiers using `test_m1.py ... test_mN.py` via pytest
- every explicit requirement/prohibition getting direct verifier coverage
- `tests/test.sh` using `set -euo pipefail`
- exact reward footer in `tests/test.sh`
- verifier dependency/runtime placement in `tests/test.sh`
- the task is still only a draft until real local checks run
```

### Cursor task creation

```text
materialize the draft into tasks/<task-name>/
{Paste_entire_initial_draft}
```


### Tighten instruction style (Attach: instruction-humanization-playbook.md)

```text
Rewrite only `instruction.md` so it sounds more like a real engineer talking to a coding agent(Use characters that are available on a typical Windows/MacBook keyboard). Keep all requirements, keep absolute paths, remove hint-like wording, and keep it concise. see `instruction-humanization-playbook.md`
```

### Tighten verifier quality

```text
Review only the verifier design. Look for answer leakage, weak assertions, missing direct schema validation for promised structured artifacts including object/dict key formats, nondeterminism, bad verifier dependency/runtime placement, missing `set -euo pipefail`, or ways an agent could pass without solving the task. Then rewrite only the affected verifier files.
```
