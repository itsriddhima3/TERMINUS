# Workflow Prompts

All prompts for the Terminal-Bench 3 task creation pipeline, in order.

## Overview

```
Step 1:  ChatGPT  → Find the idea (creative, iterative)
Step 2a: Cursor   → Validate idea + produce authoring spec + reviewer appendix (automated loop)
         [you review specs/<task-name>.md and specs/<task-name>-reviewer.md]
Step 2b: Cursor   → Create task files from the authoring spec, then confirm the discovery budget against the reviewer appendix
                     (includes discoverability gate + mechanical collapse check)
Step 3a: Cursor   → Harbor execution (oracle 10x + NOP preflight, then GPT-5.2 quality check)
Step 3b: Cursor   → Analysis & decision (collapse audit, per-test feasibility, final verdict)
```

### Setup
- **Step 1**: Attach the entire `web/` folder to ChatGPT (drag and drop all 4 files).
- **Steps 2a–3**: Open the repo in Cursor. The `.cursor/rules/` files auto-apply.

---

## Step 1: ChatGPT — Idea Generation

Use this prompt to generate and screen task ideas. Run it multiple times until you have a strong candidate.

```text
You are helping me find a strong Terminal-Bench 3 / Terminus Edition 2 task idea.

Follow the attached bundle files. This bundle is hard-only.

Rules:
- Reject class-project ideas, giant scopes, busywork, obscure-fact lookups, hidden-instance gimmicks.
- Reject ideas that are only hard because of one hidden broken file or one magic lookup.
- Reject ideas likely to collapse into policy-knob transcription, finite state-table repair, toy hardening checklists, or pre-factored recipe completion.
- Reject "implement this spec" ideas — if the concept is "write a program that does X" where X is fully specified, it's easy regardless of output complexity.
- Reject build-from-scratch on blank canvas — hard tasks need an existing system with real coupling to understand and debug.
- Reject in-distribution recipes — HMAC verification, JSON validation, Monte Carlo CI, sliding windows, policy checkers are trivial for frontier models.
- Every surviving idea must satisfy all 5 hardness axes: (1) agent must discover info not in instruction, (2) answer spans multiple interacting systems, (3) instruction describes symptoms not causes, (4) local fixes break distant invariants, (5) domain reasoning beyond training distribution.
- Avoid Python unless there is a compelling reason.
- Avoid FastAPI unless there is a compelling reason.
- Do not label ideas as `long_context`, `api_integration`, or `ui_building` unless they actually satisfy the strict criteria in the bundle.
- If no clearly hard survivor exists, say REGENERATE and produce a better batch.

For each surviving idea, provide:
- Short title (3-4 words)
- 1-2 sentence concept
- Why it is hard for a good reason
- What the verifier would check at a high level
- Biggest likely rejection risk
- Verdict: strong candidate / borderline / reject

End by naming the single best candidate.

Here is my input:

[PASTE ONE OF THE FOLLOWING]

Option A — Seed idea:
Treat this as one candidate and generate 5-8 nearby variants or alternate framings around the same real-world problem. Do not just evaluate the seed — challenge it with stronger alternatives.
[your task idea, screenshot, or a favorite from a previous batch]

Option B — Domain exploration:
Generate 8-12 fresh hard-task candidates in this domain: [your domain]
```

This step is iterative. Keep running it until you have a winner:
- "Regenerate — none of these are hard enough"
- "I like #3, give me variants around that" (paste #3 back as Option A)
- "Compare #2 and #4 — which survives better?"
- "Try a completely different domain: [new domain]" (Option B again)

Once you have a strong candidate, move to Step 2a in Cursor.

---

## Step 2a: Cursor — Validate Idea & Produce Specs

One prompt. Cursor runs a validation loop automatically using `validate_loop.py` as the decision oracle. No manual pasting between attempts.

```text
Validate this task idea and produce an authoring spec plus a separate reviewer appendix. Do NOT create any task files under tasks/.

You will run an automated validation loop. The script validate_loop.py manages the loop state and tells you what to do at each step.

Follow @idea-validation.mdc for all checks, rubric axes, and spec format.
Follow @difficulty-calibration.mdc Part A for the collapse audit.
Use `specs/validation_schema.json` as the required evidence contract for each attempt.

## Step 0: Initialize

Run:
  python validate_loop.py init <task-name>

Read the ACTION line from the output.

## Loop: repeat until ACTION is GO or STOP

### On ACTION: CONTINUE

1. Evaluate the 5 hardness axes from @idea-validation.mdc (Discover, Synthesize, Diagnose, Navigate coupling, Reason beyond training). For EACH axis, write 1-2 sentences explaining how this task satisfies it. If any axis fails, the task cannot be hard — this is a FAIL.
2. Run the instruction completeness test: "Can the agent solve this by reading ONLY instruction.md without deeply engaging with the codebase?" If yes, this is a FAIL.
3. Run all 20 anti-trivialization checks from @idea-validation.mdc. For EACH check, write 1-2 sentences of reasoning BEFORE the Pass/Warn/Fail verdict.
4. Evaluate against the 6 rubric axes. For EACH axis, write 1 sentence of reasoning and a Pass/Warn/Fail verdict. Show all 6 explicitly — do not summarize as "all pass."
5. Run the collapse audit from @difficulty-calibration.mdc Part A (full template).
6. If this is attempt 2+: for each check that was WARN or FAIL in a previous attempt and is now PASS, explicitly state what design change caused the improvement. Do not just rephrase the reasoning — name the structural change.
7. If you changed anything from the original idea beyond fixing the flagged issues (language, scope, domain, architecture, number of modules, etc.), state each change and why it was necessary.
8. Build a structured evidence JSON that matches `specs/validation_schema.json`. Populate ALL required fields. In particular:
   - `hardness_axes`
   - `anti_trivialization_checks`
   - `discovery_budget`
   - `instruction_specificity`
   - `attack_path`
   - `smallest_plausible_patch`
   The `discovery_budget` field is BLOCKING: include at least 3 non-trivial solver discoveries the finished task should force from the codebase/runtime. For each item, name the discovery, where it should live after Step 2b, and why instruction.md must not reveal it. If you cannot list 3, the idea is easy.
   The `instruction_specificity` field is BLOCKING: for a hard candidate, `level` must be `symptoms-only`. If the best honest level is `spec-complete` or `cause-revealing`, the idea cannot GO.
9. Count your FAILs and WARNs from the evidence and written review. Do not let the score contradict the structured verdicts.
10. Produce two documents using the format in @idea-validation.mdc:
    - an authoring spec for Step 2b
    - a separate reviewer appendix for human review only
    The Decision line in BOTH files must include the attempt number (e.g., "GO — Attempt 2. ...").
    Hold both docs in your context — do NOT save them yet.
11. Save the structured evidence JSON to a temporary path, for example:
      /tmp/<task-name>-validation-evidence.json
12. Record the result FIRST (this determines where to save and whether the evidence is sufficient):
      python validate_loop.py record <task-name> --evidence /tmp/<task-name>-validation-evidence.json
13. Read `SAVE_TO` and `REVIEWER_SAVE_TO` from the script's output. NOW save the authoring spec to `SAVE_TO` and the reviewer appendix to `REVIEWER_SAVE_TO`.
    Each file must contain ONLY this variant's content — no comparison tables, no previous attempt data, no clutter.
    If `SAVE_TO` is `DISCARD`, do not save either file — the attempt was a regression and should not be persisted.
    IMPORTANT: always save AFTER record, never before. The script decides whether this attempt should overwrite the best specs or go to paired candidate files.
14. Read the script's ACTION. It will say one of:
    - ACTION: CONTINUE — list your current WARNs and FAILs. For each, propose a specific concrete change (not vague — e.g., "move matvec accounting into a separate module with its own seeded defect" not "spread bugs around"). Apply ALL changes to create a new variant. Go back to step 1 of this loop with the new variant.
    - ACTION: SELECT — go to the SELECT section below.
    - ACTION: GO — go to the DONE section below.
    - ACTION: STOP — go to the DONE section below.

### On ACTION: SELECT

The script hit a plateau — multiple variants have the same score but may differ in quality.
1. Read the CANDIDATES line from the script output. Each entry is `attempt=authoring-spec|reviewer-appendix`, so you can compare the attempt number and both file paths directly.
2. Read each candidate authoring spec and reviewer appendix.
3. For each, run the collapse audit and summarize: collapse verdict, oracle complexity (lines), editable frontier (files), residual hardness (one sentence).
4. Pick the winner — the spec a reviewer would most confidently approve.
5. Tell the script (it handles promotion and cleanup automatically):
     python validate_loop.py select <task-name> --winner <attempt-number-or-listed-path>
   Examples:
   - `python validate_loop.py select <task-name> --winner 3`
   - `python validate_loop.py select <task-name> --winner specs/<task-name>-candidate-1.md`
   - `python validate_loop.py select <task-name> --winner specs/<task-name>-candidate-1-reviewer.md`

### On ACTION: GO or STOP — DONE

Report:
- Final decision: GO or STOP
- Winning attempt number (if GO)
- Stopping reason (perfect / plateau+selection / max attempts / unfixable)
- Final FAIL/WARN counts
- The authoring spec path (if GO): specs/<task-name>.md
- The reviewer appendix path (if GO): specs/<task-name>-reviewer.md

If STOP: explain why the idea family cannot be saved.

Here is the task idea:

[PASTE THE WINNING IDEA FROM STEP 1]
```

**After this runs:** Open `specs/<task-name>.md` and `specs/<task-name>-reviewer.md`. Review both. If satisfied, move to Step 2b. Drafting should consume only the authoring spec.

---

## Step 2b: Cursor — Create Task Files

Only run this after you've reviewed and approved the Step 2a authoring spec and reviewer appendix.

```text
Create a new task from the authoring spec file below.
Follow @task-creation.mdc for all file rules.

Read ONLY the authoring spec file while drafting the task. Do NOT open the reviewer appendix during drafting.

Use the authoring spec's metadata, public contract, failure topology, environment shape, required artifacts, and test plan to create all task files. The brief is intentionally non-exhaustive: you must design the exact internal file tree and implementation scaffolding yourself while preserving the brief's public contract and difficulty profile.

Place files under tasks/<task-name>/ (get the task name from the authoring spec's Metadata section).

## File creation

Create the files required by the brief and by @task-creation.mdc. The exact file set depends on task type:

**Standard tasks (most tasks):**
- tests/test_outputs.py — implement test plan, target 6+ tests
- tests/test.sh — start from the standard platform template in @task-creation.mdc and preserve its command order/control flow; only the documented semantic variations are allowed

**Milestone tasks (number_of_milestones > 0):**
- tests/test_m1.py, tests/test_m2.py, ... — one test file per milestone
- tests/test.sh — start from the standard platform template in @task-creation.mdc and preserve its command order/control flow; only the documented semantic variations are allowed

**UI tasks (subcategories includes ui_building):**
- tests/test_outputs.py — unit tests
- tests/ e2e test files — Playwright/Vitest as specified in @task-creation.mdc
- tests/test.sh — copy the UI platform template from @task-creation.mdc (different from standard)

**All task types:**
- instruction.md — write human-style per humanization rules in @task-creation.mdc
- task.toml — fill in all metadata from the authoring spec
- output_contract.toml — declare `user_visible_outputs`, `structured_outputs`, and `internal_harness_files`. The instruction must cover only the declared user-visible outputs and schemas; do not mention a literal `internal_harness_files` path in instruction.md unless that same path is also declared in `user_visible_outputs`.
- environment/Dockerfile — pin FROM by digest, pin apt versions
- solution/solve.sh — implement a deterministic oracle consistent with the authoring spec (set -euo pipefail for solve.sh only)
- All environment source files required by the authoring spec's environment shape and your chosen internal design

Check @task-creation.mdc for the correct template and file layout for your task type.

## Discovery budget confirmation (mandatory, run after all files exist)

Only after the task files exist, open the reviewer appendix. Use it ONLY for this confirmation step — not for initial drafting.

For each `Discovery budget` item in the reviewer appendix:
1. Confirm the discovery still exists in the built task and is still something the solver must recover from code/runtime behavior.
2. Confirm it lives in the planned location, or note the equivalent location you actually created.
3. Confirm instruction.md, file names, test names, comments, fixtures, and obvious runtime errors do NOT reveal it directly.

If any discovery disappeared, moved into an obvious single-file breadcrumb, or is now revealed by the solver-visible file surfaces or obvious runtime errors, revise the task and re-check the entire budget.

Report each discovery and how you confirmed it still survives.

## Discoverability gate (mandatory, run after all files exist)

Before finishing, use the solver-visible file-surface policy from `@task-creation.mdc`: the agent can inspect `instruction.md`, everything under `environment/`, everything under `tests/`, and the file/directory names within those surfaces. On the current repo policy, `task.toml` and `output_contract.toml` are authoring/package metadata and are NOT solver-visible for this gate.

Ask yourself — could the agent skip the hard reasoning and find the solution through surface-level signals in any of those file surfaces? If you run the broken task during review, also ask whether runtime error output leaks the fix.

1. Does the instruction point to specific code locations or implementation details instead of describing required behavior?
2. Do source/config/data files under `environment/` contain markers, flags, annotations, commented-out correct values, or structural hints that reveal fix locations or correct values?
3. Do file or directory names describe what's broken or what to fix?
4. Do test names or assertions reveal the solution steps rather than just what to verify?
5. If you ran the broken task, would runtime error output pinpoint the exact fix rather than just indicating something is wrong?

If ANY answer is yes: identify the signal and eliminate it. Then re-verify oracle still passes.

Report what you checked and what you changed (if anything).

## Static checks

After everything is finalized, run the task-scoped static checker. It covers repo-local structural/compliance rules only; it does not replace `collapse_check.py`, the Harbor quality check, or the final approval decision:
  python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2

Then verify the environment file count (excluding Dockerfile/docker-compose):
  find tasks/<task-name>/environment -type f ! -iname 'Dockerfile' ! -iname 'docker-compose*' | wc -l

This must be 20 or more. Under 20 is a blocking failure: the task is `minimal`, which is rejected on the default Edition 2 path. Treat this as a minimum realism floor, not as evidence that the task is hard. If under 20, add genuine source modules, headers, data files, or config files that the task actually needs. Do not hover at exactly 20, and do not add empty or trivial padding files.

Report any failures and fix them.

## Mechanical collapse gate (BLOCKING — run after static checks pass)

Run the automated collapse/discoverability checker:
  python3 collapse_check.py tasks/<task-name>

This checks 5 root-cause signals: oracle simplification, oracle predictability, verifier shallowness, tamper surface, and agent-visible reference artifacts on the solver-visible file surfaces from `@task-creation.mdc` (`instruction.md`, `tests/`, and `environment/`; excluding `task.toml` and `output_contract.toml`). Predictability now considers visible artifact file names and explicit test names in addition to instruction keywords. Reference-artifact/tamper checks also look for answer-shaped verifier material such as hardcoded digest/checksum targets and large inline or generated shadow simulators/state machines. Oracle/frontier analysis is transitive: it follows solution-local called scripts, patch hunks, heredoc writes, in-place shell rewrites (`sed -i`, `perl -0pi`, temp-file rewrite + `mv`, `cp`/`install` replacements), and simple inline Python rewrite/write patterns instead of only grepping `solution/solve.sh`.

- **FAIL (exit 1):** At least one fatal signal. Fix the flagged issue before proceeding to Step 3a. Common fixes: rename files/directories to not encode the task contract, restructure oracle so it does real work instead of collapsing to no-ops, add output validation to tests so exit-code-only cheating doesn't work, and remove answer-shaped artifacts from solver-visible files.
- **WARN (exit 2):** Non-fatal signals that need justification. Proceed to Step 3a but document why each WARN is acceptable in your report.
- **PASS (exit 0):** No signals. Proceed to Step 3a.

Do NOT proceed to Step 3a with a collapse_check.py FAIL. Fix the issues first, re-run static checks, re-run collapse_check.py, and only proceed when it returns PASS or WARN.

Authoring spec path: [PASTE THE PATH e.g. specs/block-krylov-resume.md]
Reviewer appendix path: [PASTE THE PATH e.g. specs/block-krylov-resume-reviewer.md]
```

---

## Step 3a: Cursor — Harbor Execution

Run all harbor commands. This step is purely execution — no analysis or decisions yet.

```text
Run harbor validation for the task. You are allowed to run shell commands. Start from the project root.

### 1. Preflight (oracle + NOP may run in parallel in separate terminals)
Oracle stress test (10 parallel runs — no API key needed):
  harbor run -p "tasks/<task-name>" -a oracle -k 10

ALL 10 must score 1.0. Any failure = oracle is broken or flaky. Report exact scores.

NOP baseline (no API key needed):
  harbor run -p "tasks/<task-name>" -a nop

Must score 0.0. If it scores above 0.0, the verifier accepts the broken baseline.
You may launch oracle and NOP at the same time, but do not edit task files during either run.

### 2. Source OpenAI API key (needed for the GPT-5.2 quality check)
  set -a && source .env && set +a
If .env is missing or does not contain an OpenAI API key, state so and skip step 3. Oracle and NOP results above are still valid; the mechanical stack in Step 3b will still run.

### 3. Quality check (requires OpenAI API key)
Only after Oracle and NOP pass:
  harbor tasks check "tasks/<task-name>" -m "openai/gpt-5.2"

Report ALL results. Any ❌ fail on behavior_in_task_description, behavior_in_tests, or anti_cheating_measures is a HIGH-severity finding that MUST be repaired before proceeding.

If quality check reports HIGH failures: fix them, then rerun ALL prior steps (oracle -k 10, NOP) to confirm they still pass with the modified files, then rerun the quality check. Do not proceed to Step 3b with unrepaired HIGH findings or stale oracle/NOP evidence.

If no OpenAI API key in .env, state that quality check was skipped due to missing API key.

### 4. Fix and rerun
If any harbor step fails or reports HIGH findings, fix the issue and rerun from step 1 (preflight). Every step's evidence must reflect the current state of task files — never carry forward results from before an edit.

## Constraints
- Do not claim any command passed unless it was actually run.
- Show the exact output of each harbor command.
- If harbor tasks check is blocked by Oracle/NOP failure, say so.
- Do not run `verifier_health.py` concurrently with Step 3a harbor runs on the same task path; it launches extra oracle jobs during Step 3b.

## Required output
1. Oracle result: N/10 passed, any failures
2. NOP result: score
3. Quality check: full result, list any ❌ fail findings
4. What you fixed and why (if anything)
5. Whether any task files were edited during this step (triggers full rerun)

Task path: tasks/<task-name>
```

---

## Step 3b: Cursor — Analysis & Decision

Run after Step 3a completes. This step is primarily analysis, but if you fix any issues, you must revalidate.

**DIRTY-FLAG RULE: If you edit ANY file under `tasks/<task-name>/` during this step (tests, instruction, oracle, environment, metadata) and do NOT restore it to byte-identical state, you MUST rerun Step 3a before making a final decision. Do not approve using pre-edit oracle, NOP, or quality check results. State which files changed and why rerun is needed. Temp-copy automation from `verifier_health.py` does not trigger this rule by itself.**

```text
Analyze the task for collapse, feasibility, and discoverability. Use results from Step 3a.
Follow @review-and-submit.mdc and @difficulty-calibration.mdc for all rules — do not rely on behavioral descriptions in this prompt.

Track whether you edit any task files. If you do, you must rerun Step 3a before the final decision.

### 1. Mechanical collapse check
  python3 collapse_check.py tasks/<task-name>

FAIL = blocking. Fix the flagged issues, re-run collapse_check.py, and re-run oracle from Step 3a to confirm it still passes.
WARN = document justification for each signal.

### 2. Structural review
Review against @review-and-submit.mdc checklist. Fix any issues.

Mandatory: compare tests/test.sh against the official platform template in @task-creation.mdc for semantic compliance. Standard and UI tasks have different templates — check which applies.

Mandatory: verify environment file count:
  find tasks/<task-name>/environment -type f ! -iname 'Dockerfile' ! -iname 'docker-compose*' | wc -l
Must be 20+. Verify codebase_size in task.toml matches (see @review-and-submit.mdc § Task Metadata).

### 3. Collapse audit (LLM-level)
Run @difficulty-calibration.mdc Part A on the actual drafted files. Report the full template:
- smallest plausible successful patch
- likely editable frontier
- requirement-to-file map
- oracle line count (non-boilerplate)
- discoverability analysis
- red flags
- residual hardness
- collapse verdict (PASS / WARN / FAIL)

**Discoverability dimension:** Patch SIZE (how much work) and patch FINDABILITY (can the agent locate where to work without domain understanding) are both required. A 200-line oracle across 7 files is still trivial if any channel tells the agent where to look.

### 4. Per-test feasibility
Run @difficulty-calibration.mdc Part B:
- Per-test feasibility template for each test function
- Flag any HIGH-risk tests
- Run verifier health automation and inspect its JSON/text output:
  `python3 verifier_health.py --task-dir tasks/<task-name> --output-json /tmp/<task-name>-verifier-health.json`
  This one command covers randomized-order verifier runs, repeated oracle consistency, and temp-copy partial-oracle ablations.
  **BLOCKING: if `verifier_health.py` exits nonzero, stop and fix the reported issue. Compile-only partial-oracle failures do not count as verifier discrimination.**
- Propose fixes for any HIGH-risk tests

`verifier_health.py` uses temporary task copies, so it does not trigger the dirty-flag rule unless you separately edit real files under `tasks/<task-name>/`.

### 5. Final decision

**Before deciding:** Did you edit any file under tasks/<task-name>/ during steps 1-4 above?
- If YES: state which files changed, then STOP. Report: "Cannot make final decision — task files were modified. Rerun Step 3a." Do not approve, reject, or send feedback using pre-edit evidence.
- If NO: proceed to the decision.

Before any `APPROVE`, `APPROVE WITH NOTE`, or "ready" claim, package the task and run:
  python3 approve_task.py --task-dir tasks/<task-name> --zip Task_Ready_To_Submit/<task-name>.zip --verifier-health /tmp/<task-name>-verifier-health.json

If `approve_task.py` exits nonzero, report its blocking failures and stop. Do not override it with prose.

Use the Decision Criteria from @review-and-submit.mdc (APPROVE / APPROVE WITH NOTE / REJECT / SEND FEEDBACK). Apply all blocking conditions from that file. Do not restate the criteria here — read them from the rule file.

## Required report
1. Overall decision (APPROVE / APPROVE WITH NOTE / REJECT / SEND FEEDBACK)
2. collapse_check.py result (PASS/WARN/FAIL + details)
3. Collapse audit verdict with full template
4. Difficulty estimate with evidence
5. Discoverable test count
6. Oracle result (from Step 3a)
7. NOP result (from Step 3a)
8. Quality check result (from Step 3a)
9. Per-test feasibility flags
10. Verifier health results (repeat oracle, randomized order, partial-oracle classifications)
11. Highest-severity findings first
12. Classify each finding as concept-level or mechanical/compliance-level
13. What you changed and why

Task path: tasks/<task-name>
```

---

## After Step 3b: Package & Submit

Once the review passes:

```bash
cd tasks/<task-name>
rm -f ../../Task_Ready_To_Submit/<task-name>.zip
zip -rq ../../Task_Ready_To_Submit/<task-name>.zip . -x '*/__pycache__/*' '*.pyc' '.*'
python3 ../../validate_submission_zip.py ../../Task_Ready_To_Submit/<task-name>.zip
python3 ../../verifier_health.py --task-dir ../../tasks/<task-name> --output-json /tmp/<task-name>-verifier-health.json
python3 ../../approve_task.py --task-dir ../../tasks/<task-name> --zip ../../Task_Ready_To_Submit/<task-name>.zip --verifier-health /tmp/<task-name>-verifier-health.json
```

Verify: `instruction.md`, `task.toml`, `output_contract.toml`, `environment/`, `solution/`, and `tests/` at archive root.

Platform submission:
1. Upload zip. Check "Generate rubric". Uncheck "Send to reviewer". Submit.
2. Wait for CI to return the generated rubric.
3. Edit the rubric for accuracy.
4. Uncheck "Generate rubric". Check "Send to reviewer". Submit.
