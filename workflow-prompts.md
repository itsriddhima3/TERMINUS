# Workflow Prompts

All prompts for the Terminal-Bench 3 task creation pipeline, in order.

## Overview

```
Step 1:  ChatGPT  → Find the idea (creative, iterative)
Step 2a: Cursor   → Validate idea + produce spec (automated loop)
         [you review specs/<task-name>.md]
Step 2b: Cursor   → Create task files from the saved spec
Step 3:  Cursor   → Review, repair, validate, package
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
3. Run all 18 anti-trivialization checks from @idea-validation.mdc. For EACH check, write 1-2 sentences of reasoning BEFORE the Pass/Warn/Fail verdict.
4. Evaluate against the 6 rubric axes. For EACH axis, write 1 sentence of reasoning and a Pass/Warn/Fail verdict. Show all 6 explicitly — do not summarize as "all pass."
5. Run the collapse audit from @difficulty-calibration.mdc Part A (full template).
6. If this is attempt 2+: for each check that was WARN or FAIL in a previous attempt and is now PASS, explicitly state what design change caused the improvement. Do not just rephrase the reasoning — name the structural change.
7. If you changed anything from the original idea beyond fixing the flagged issues (language, scope, domain, architecture, number of modules, etc.), state each change and why it was necessary.
8. Count your FAILs and WARNs.
9. Produce the spec using the format in @idea-validation.mdc. The Decision line must include the attempt number (e.g., "GO — Attempt 2. ...").
10. Read the SAVE_TO path from the last script output. Save the spec to that path.
    The spec file must contain ONLY this variant's spec — no comparison tables, no previous attempt data, no clutter.
11. Record the result:
      python validate_loop.py record <task-name> --fails N --warns N
12. Read the script's output. It will say one of:
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
5. Copy the winning spec to specs/<task-name>.md. Delete the other candidate files.
6. Tell the script:
     python validate_loop.py select <task-name> --winner N
   (where N is the winning attempt number)

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

Create all files described in the spec:
- instruction.md: write it human-style per the humanization rules in @task-creation.mdc. Use the spec's instruction summary as the contract but write it in your own voice.
- task.toml: fill in all metadata from the spec.
- environment/Dockerfile: pin FROM by digest. Pin apt versions.
- solution/solve.sh: implement the oracle approach from the spec. Use set -euo pipefail (solve.sh only — test.sh must NOT use it).
- tests/test_outputs.py: implement the test plan from the spec. Target 6+ discoverable tests.
- tests/test.sh: copy the official platform template from @task-creation.mdc exactly.
- All environment source files described in the spec.

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

Report any failures and fix them before moving to Step 3.

Spec file path: [PASTE THE PATH e.g. specs/block-krylov-resume.md]
```

---

## Step 3: Cursor — Review & Repair

Paste this after task creation is complete.

```text
Review and repair the task following @review-and-submit.mdc and @difficulty-calibration.mdc.
You are allowed to run shell commands. Start from the project root.

## Execution procedure

### Phase 1: Structural review
Review against @review-and-submit.mdc. Fix any issues found.

Mandatory: compare `tests/test.sh` against the official platform template in @task-creation.mdc.
- **Standard tasks:** CI checker validates the last 6 lines must be `if [ $? -eq 0 ]; then` / reward writes / `fi`. No `set -euo pipefail`, no `set +e`, no `$status`, no `exit` after `fi`. If any mismatch, rewrite from the template.
- **UI tasks:** Use the separate UI template (with `set -e`, `UNIT_EXIT`/`E2E_EXIT`, final assertion). CI checker skips the strict tail check for UI tasks.

Mandatory: verify environment file count:
  find tasks/<task-name>/environment -type f ! -iname 'Dockerfile' ! -iname 'docker-compose*' | wc -l
Must be 20+. Under 20 = "minimal" which is blocked on the platform. If under 20, warn the user. Verify `codebase_size` in task.toml matches the actual count (20-200 = small, 200+ = large). Tasks at exactly 20 should be flagged as borderline.

### Phase 2: Collapse audit + discoverability
Run @difficulty-calibration.mdc Part A on the actual drafted files. Report:
- smallest plausible successful patch
- likely editable frontier
- requirement-to-file map
- oracle line count (non-boilerplate)
- red flags
- residual hardness
- collapse verdict (PASS / WARN / FAIL)

**Discoverability dimension:** The collapse audit has two dimensions — patch SIZE (how much work) and patch FINDABILITY (can the agent locate where and what to work on without domain understanding). A 200-line oracle across 7 files is still trivial if any channel tells the agent where to look.

Put yourself in the agent's position. It has instruction.md, environment/, and at runtime tests/ and error output. Ask:
- Could surface-level signals in ANY channel (instruction wording, source code, file names, test names, error messages, metadata, comments) shortcut the domain reasoning this task demands?
- Would a strong model's first attempt likely succeed without deep understanding of the problem domain?

If discoverability risk found: fix the signals, then re-verify oracle+NOP.
If collapse verdict is FAIL: stop and recommend redesign.

### Phase 3: Oracle + NOP
Run Oracle 3x to catch flakiness:
  cd <project_root> && harbor run -p "<task_path>" -a oracle
Run NOP:
  cd <project_root> && harbor run -p "<task_path>" -a nop

Oracle must score 1.0. NOP must score 0.0.

### Phase 4: Per-test feasibility
Run @difficulty-calibration.mdc Part B:
- Per-test feasibility template for each test function
- Flag any HIGH-risk tests
- Run test order independence check (pytest with random order)
- Run flaky stress-test: run full test suite 5+ times after oracle passes, flag any intermittent failures
- Partial-oracle simulation: comment out ~30% of solve.sh, run tests, report which pass
  **BLOCKING: if ALL tests still pass under partial oracle, the verifier doesn't discriminate. Fix the tests so at least one fails before proceeding. Do not approve with a note.**
- Propose fixes for any HIGH-risk or flaky tests

### Phase 5: Harbor tasks check
Only after Oracle and NOP pass:
  cd <project_root> && set -a && source .env && set +a && harbor tasks check "<task_path>" -m "anthropic/claude-sonnet-4-6"

If no API key in .env or source fails, state that harbor tasks check was skipped due to missing API key.

### Phase 6: Agent trials (if API key available)
Source the API key and run agent trials (1 minimum, 3 preferred, 5 maximum):
  cd <project_root> && set -a && source .env && set +a && harbor run -p "<task_path>" -a terminus-2 -m "anthropic/claude-opus-4-6"

Run the above command at least once, ideally 3-5 times (maximum 5). Build per-test pass matrix from the results.
If any test is 0/N across all trials, investigate and fix.
**BLOCKING: if pass rate >80% across 3-5 trials, the task is too easy. Harden or redesign before approving. Do not approve with a note.**
If no API key in .env, state that difficulty is estimated, not empirical.

### Phase 7: Fix and rerun
Fix issues found in any phase and rerun the relevant checks.

## Constraints
- Do not claim any command passed unless it was actually run.
- If harbor tasks check is blocked by Oracle/NOP failure, say so clearly.
- Report discoverable test count explicitly.
- Show diffs for any edited files.

## Required report

1. Overall decision — follow the Decision Criteria in @review-and-submit.mdc exactly:
   - APPROVE: all gates pass, no concept-level issues, partial-oracle fails at least one test
   - APPROVE WITH NOTE: only when collapse is WARN (not FAIL), no blocking conditions, agent trials not run
   - REJECT: collapse FAIL, oracle broken, NOP passes, or 3-5 agent trials >80%
   - SEND FEEDBACK: concept strong but implementation needs rework
   **Do NOT use APPROVE WITH NOTE to defer concept-level problems (partial-oracle passes all tests, discoverability signals unfixed, agent trial 1.0 without more trials).**
2. Difficulty estimate with evidence
3. Discoverable test count
4. Collapse audit verdict with full template
5. Oracle result (pass/fail, run count)
6. NOP result
7. Per-test feasibility flags (any HIGH-risk tests with recommendations)
8. Partial-oracle simulation results
9. harbor tasks check result
10. Per-test pass matrix (if agent trials were run)
11. Highest-severity findings first
12. Classify each finding as concept-level or mechanical/compliance-level
13. What you changed and why
```

---

## After Step 3: Package & Submit

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
