# Workflow Prompts

All prompts for the Terminal-Bench 3 task creation pipeline, in order.

## Overview

```
Step 1:  ChatGPT  → Find the idea (creative, iterative)
Step 2a: Cursor   → Validate idea + produce spec (automated loop)
         [you review specs/<task-name>.md]
Step 2b: Cursor   → Create task files from the saved spec
                     (includes discoverability gate + mechanical collapse check)
Step 3a: Cursor   → Harbor execution (oracle 10x, NOP, quality check, agent trials 5x)
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

## Step 2a: Cursor — Validate Idea & Produce Spec

One prompt. Cursor runs a validation loop automatically using `validate_loop.py` as the decision oracle. No manual pasting between attempts.

```text
Validate this task idea and produce a spec. Do NOT create any task files under tasks/.

You will run an automated validation loop. The script validate_loop.py manages the loop state and tells you what to do at each step.

Follow @idea-validation.mdc for all checks, rubric axes, and spec format.
Follow @difficulty-calibration.mdc Part A for the collapse audit.

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
8. Count your FAILs and WARNs.
9. Produce the spec using the format in @idea-validation.mdc. The Decision line must include the attempt number (e.g., "GO — Attempt 2. ...").
   Hold the spec in your context — do NOT save it yet.
10. Record the result FIRST (this determines where to save):
      python validate_loop.py record <task-name> --fails N --warns N
11. Read SAVE_TO from the script's output. NOW save the spec to that path.
    The spec file must contain ONLY this variant's spec — no comparison tables, no previous attempt data, no clutter.
    If SAVE_TO is DISCARD, do not save — the attempt was a regression and should not be persisted.
    IMPORTANT: always save AFTER record, never before. The script decides whether this attempt should overwrite the best spec or go to a candidate file.
12. Read the script's ACTION. It will say one of:
    - ACTION: CONTINUE — list your current WARNs and FAILs. For each, propose a specific concrete change (not vague — e.g., "move matvec accounting into a separate module with its own seeded defect" not "spread bugs around"). Apply ALL changes to create a new variant. Go back to step 1 of this loop with the new variant.
    - ACTION: SELECT — go to the SELECT section below.
    - ACTION: GO — go to the DONE section below.
    - ACTION: STOP — go to the DONE section below.

### On ACTION: SELECT

The script hit a plateau — multiple variants have the same score but may differ in quality.
1. Read the CANDIDATES line from the script output. It lists the spec files to compare.
2. Read each candidate spec file.
3. For each, run the collapse audit and summarize: collapse verdict, oracle complexity (lines), editable frontier (files), residual hardness (one sentence).
4. Pick the winner — the spec a reviewer would most confidently approve.
5. Tell the script (it handles promotion and cleanup automatically):
     python validate_loop.py select <task-name> --winner N
   (where N is the winning attempt number from the CANDIDATES list)

### On ACTION: GO or STOP — DONE

Report:
- Final decision: GO or STOP
- Winning attempt number (if GO)
- Stopping reason (perfect / plateau+selection / max attempts / unfixable)
- Final FAIL/WARN counts
- The spec file path (if GO): specs/<task-name>.md

If STOP: explain why the idea family cannot be saved.

Here is the task idea:

[PASTE THE WINNING IDEA FROM STEP 1]
```

**After this runs:** Open `specs/<task-name>.md` and review it. If satisfied, move to Step 2b.

---

## Step 2b: Cursor — Create Task Files

Only run this after you've reviewed and approved the spec from Step 2a.

```text
Create a new task from the spec file below.
Follow @task-creation.mdc for all file rules.

Read the spec file. Use its file tree, metadata, instruction summary, test plan, and oracle approach to create all task files.

Place files under tasks/<task-name>/ (get the task name from the spec's Metadata section).

## File creation

Create all files described in the spec. The exact file set depends on task type:

**Standard tasks (most tasks):**
- tests/test_outputs.py — implement test plan, target 6+ tests
- tests/test.sh — copy the standard platform template from @task-creation.mdc exactly

**Milestone tasks (number_of_milestones > 0):**
- tests/test_m1.py, tests/test_m2.py, ... — one test file per milestone
- tests/test.sh — copy the standard platform template from @task-creation.mdc exactly

**UI tasks (subcategories includes ui_building):**
- tests/test_outputs.py — unit tests
- tests/ e2e test files — Playwright/Vitest as specified in @task-creation.mdc
- tests/test.sh — copy the UI platform template from @task-creation.mdc (different from standard)

**All task types:**
- instruction.md — write human-style per humanization rules in @task-creation.mdc
- task.toml — fill in all metadata from the spec
- environment/Dockerfile — pin FROM by digest, pin apt versions
- solution/solve.sh — implement oracle approach from spec (set -euo pipefail for solve.sh only)
- All environment source files described in the spec

Check @task-creation.mdc for the correct template and file layout for your task type.

## Discoverability gate (mandatory, run after all files exist)

Before finishing, put yourself in the agent's position. It has never seen the spec, the oracle, or your reasoning. It only has what's in the task: instruction.md, everything under environment/, and at runtime it can see tests/ and error output.

Ask yourself — could the agent skip the hard reasoning and find the solution through surface-level signals in ANY of these channels?

1. Does the instruction point to specific code locations or implementation details instead of describing required behavior?
2. Does the source code contain markers, flags, annotations, or structural hints that reveal fix locations or correct values?
3. Do file or directory names describe what's broken or what to fix?
4. Do test names or assertions reveal the solution steps rather than just what to verify?
5. Would error messages from running the broken code pinpoint the exact fix rather than just indicating something is wrong?

If ANY answer is yes: identify the signal and eliminate it. Then re-verify oracle still passes.

Report what you checked and what you changed (if anything).

## Static checks

After everything is finalized, run (use run_static_checks.py as the primary checker — it is task-scoped):
  python3 run_static_checks.py --task-dir tasks/<task-name> --version edition_2

Then verify the environment file count (excluding Dockerfile/docker-compose):
  find tasks/<task-name>/environment -type f ! -iname 'Dockerfile' ! -iname 'docker-compose*' | wc -l

This must be 20 or more. Under 20 = "minimal" codebase which is blocked on the platform. If under 20, add source modules, headers, data files, or config files. Aim for 25-30+ — do not design tasks that hover at exactly 20. Do not add empty or trivial padding files — each file should serve a purpose in the task.

Report any failures and fix them.

## Mechanical collapse gate (BLOCKING — run after static checks pass)

Run the automated collapse/discoverability checker:
  python3 collapse_check.py tasks/<task-name>

This checks 7 mechanical signals: grep-collapse, oracle no-op ratio, edit frontier size, oracle locality, harness editability, pre-factored helpers, oracle line count.

- **FAIL (exit 1):** At least one fatal signal. Fix the flagged issue before proceeding to Step 3a. Common fixes: rename files/directories to not encode the task contract, restructure oracle to not be all no-ops, add output validation to tests so exit-code-only cheating doesn't work, spread oracle edits across more directories.
- **WARN (exit 2):** Non-fatal signals that need justification. Proceed to Step 3a but document why each WARN is acceptable in your report.
- **PASS (exit 0):** No signals. Proceed to Step 3a.

Do NOT proceed to Step 3a with a collapse_check.py FAIL. Fix the issues first, re-run static checks, re-run collapse_check.py, and only proceed when it returns PASS or WARN.

Spec file path: [PASTE THE PATH e.g. specs/block-krylov-resume.md]
```

---

## Step 3a: Cursor — Harbor Execution

Run all harbor commands. This step is purely execution — no analysis or decisions yet.

```text
Run harbor validation for the task. You are allowed to run shell commands. Start from the project root.

### 1. Oracle stress test (10 parallel runs — no API key needed)
  harbor run -p "tasks/<task-name>" -a oracle -k 10

ALL 10 must score 1.0. Any failure = oracle is broken or flaky. Report exact scores.

### 2. NOP baseline (no API key needed)
  harbor run -p "tasks/<task-name>" -a nop

Must score 0.0. If it scores above 0.0, the verifier accepts the broken baseline.

### 3. Source API key (needed for quality check and agent trials)
  set -a && source .env && set +a
If .env is missing or does not contain an API key, state so and skip steps 4 and 5. Oracle and NOP results above are still valid.

### 4. Quality check (requires API key)
Only after Oracle and NOP pass:
  harbor tasks check "tasks/<task-name>" -m "anthropic/claude-opus-4-6"

Report ALL results. Any ❌ fail on behavior_in_task_description, behavior_in_tests, or anti_cheating_measures is a HIGH-severity finding that MUST be repaired before proceeding.

If quality check reports HIGH failures: fix them, then rerun ALL prior steps (oracle -k 10, NOP) to confirm they still pass with the modified files, then rerun the quality check. Do not proceed to agent trials with unrepaired HIGH findings or stale oracle/NOP evidence.

If no API key in .env, state that quality check was skipped due to missing API key.

### 5. Agent trials (5 parallel runs)
Only after quality check passes or HIGH findings are repaired:
  harbor run -p "tasks/<task-name>" -a terminus-2 -m "anthropic/claude-opus-4-6" -k 5

Report: mean score, per-trial scores, total time.

After trials complete, extract per-test pass/fail data from the trial's job directory.
Harbor prints the job directory in its output (e.g., `jobs/2026-04-13__16-41-36/`). Use that exact path:
  find <job-dir>/ -name "*.json" -path "*/ctrf/*"
Read each CTRF report to build a per-test pass matrix (test name × trial → pass/fail).
Do NOT use a broad `find jobs/` — that mixes results from old runs.
If any test is 0/N across all trials, flag it — that test may be too hard or broken.

If no API key in .env, state that agent trials were skipped.

### 6. Fix and rerun
If any harbor step fails or reports HIGH findings, fix the issue and rerun from step 1 (oracle). Every step's evidence must reflect the current state of task files — never carry forward results from before an edit.

## Constraints
- Do not claim any command passed unless it was actually run.
- Show the exact output of each harbor command.
- If harbor tasks check is blocked by Oracle/NOP failure, say so.

## Required output
1. Oracle result: N/10 passed, any failures
2. NOP result: score
3. Quality check: full result, list any ❌ fail findings
4. Agent trial results: per-trial scores, mean, time
5. Per-test pass matrix (test name × trial → pass/fail) — from CTRF logs
6. What you fixed and why (if anything)
7. Whether any task files were edited during this step (triggers full rerun)

Task path: tasks/<task-name>
```

---

## Step 3b: Cursor — Analysis & Decision

Run after Step 3a completes. This step is primarily analysis, but if you fix any issues, you must revalidate.

**DIRTY-FLAG RULE: If you edit ANY file under `tasks/<task-name>/` during this step (tests, instruction, oracle, environment, metadata) and do NOT restore it to byte-identical state, you MUST rerun Step 3a before making a final decision. Do not approve using pre-edit oracle, NOP, quality check, or agent trial results. State which files changed and why rerun is needed. Byte-identical restores (e.g., partial-oracle simulation with backup/restore) do not trigger this rule.**

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

Mandatory: compare tests/test.sh against the official platform template in @task-creation.mdc. Standard and UI tasks have different templates — check which applies.

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
- Run test order independence check (pytest with random order)
- Partial-oracle simulation using the non-dirty procedure below
  **BLOCKING: if ALL tests still pass under partial oracle, fix tests so at least one fails.**
- Propose fixes for any HIGH-risk tests

**Partial-oracle procedure (does NOT trigger the dirty-flag rule):**
To avoid triggering a full Step 3a rerun, use a temp copy of solve.sh:
```
cp tasks/<task-name>/solution/solve.sh /tmp/solve.sh.bak
# Edit solve.sh: comment out ~30% of fixes
harbor run -p "tasks/<task-name>" -a oracle
# Record which tests pass/fail
cp /tmp/solve.sh.bak tasks/<task-name>/solution/solve.sh
```
Because solve.sh is byte-identical restored before the final decision, this does not count as a task-file edit. Do NOT leave a modified solve.sh in place.

### 5. Final decision

**Before deciding:** Did you edit any file under tasks/<task-name>/ during steps 1-4 above?
- If YES: state which files changed, then STOP. Report: "Cannot make final decision — task files were modified. Rerun Step 3a." Do not approve, reject, or send feedback using pre-edit evidence.
- If NO: proceed to the decision.

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
10. Partial-oracle simulation results
11. Per-test pass matrix (if agent trials were run)
12. Highest-severity findings first
13. Classify each finding as concept-level or mechanical/compliance-level
14. What you changed and why

Task path: tasks/<task-name>
```

---

## After Step 3b: Package & Submit

Once the review passes:

```bash
cd tasks/<task-name>
rm -f ../../Task_Ready_To_Submit/<task-name>.zip
zip -rq ../../Task_Ready_To_Submit/<task-name>.zip . -x '*/__pycache__/*' '*.pyc' '.*'
unzip -l ../../Task_Ready_To_Submit/<task-name>.zip
```

Platform submission:
1. Upload zip. Check "Generate rubric". Uncheck "Send to reviewer". Submit.
2. Wait for CI to return the generated rubric.
3. Edit the rubric for accuracy.
4. Uncheck "Generate rubric". Check "Send to reviewer". Submit.
