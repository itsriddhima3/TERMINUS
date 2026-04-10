# Task Proposal Rubric

Use this file to judge whether a proposed Terminal-Bench 3 / Terminus Edition 2 task idea is worth drafting.

This rubric is for phase-1 idea screening. It is not the final implementation review.

## Goal

Your job is to evaluate the task proposal as presented and decide whether it appears strong enough to continue.

- focus on whether the idea is likely to become a strong benchmark task
- be skeptical of ideas that are only hard because of hidden-instance discovery, giant scope, or subjective grading
- do not redesign the task for the user unless they explicitly ask for improvement work elsewhere

## Important Note on Rubric Text

If the user later asks for rubric lines to paste into the platform UI:

- return plain chat text only
- do not create `rubrics.txt` or `rubric.txt`
- allowed score magnitudes are only `1`, `2`, `3`, and `5`
- valid rubric scores are only `+1`, `+2`, `+3`, `+5`, `-1`, `-2`, `-3`, and `-5`

## Decision Scale

Use exactly one of:

- `Strong Reject`
- `Reject`
- `Uncertain`
- `Accept`
- `Strong Accept`

## The Six Criteria

Every candidate task should be evaluated on these six axes.

### 1. Verifiable

Ask:

- can the task be checked programmatically and reliably?
- will repeated verifier runs give the same answer?
- is the verifier judging observable outcomes rather than guesses about implementation?

Warning signs:

- subjective grading
- flaky nondeterministic checks
- hidden judgement calls
- checks that depend on timing or unstable environment behavior

### 2. Well-specified

Ask:

- could two reasonable people read the prompt and build roughly equivalent verifiers?
- is every tested behavior likely to be stated honestly in the task?
- is the task concise without becoming vague?

Warning signs:

- the prompt needs too many corner cases to be safe
- the task becomes easy only if the author hides what the tests check
- the specification depends on implied behavior instead of explicit contract text

### 3. Solvable

Ask:

- is there a plausible path to a real solution?
- could an expert who already knows the approach implement it in a few hours?
- is the task asking for legitimate engineering rather than an unsolved research problem?

Warning signs:

- the task is probably impossible
- the task would need enormous amounts of code or labor
- the intended solution depends on one obscure fact rather than engineering work

### 4. Difficult

Ask:

- is the task hard for a good reason?
- does it require real systems, debugging, security, scientific, or engineering judgment?
- would the task still be hard if the prompt honestly stated the checked behavior?

Warning signs:

- course-project difficulty
- busywork or volume masquerading as difficulty
- one hidden corrupted item is doing most of the work
- the likely fix is one tiny obvious patch

### 5. Interesting / Valuable

Ask:

- does the task model something a real engineer might care about?
- would some real group of users find the problem meaningful?
- is the scenario grounded in plausible engineering work?

Warning signs:

- gimmicks
- purely synthetic puzzle flavor
- nobody would care outside the benchmark

### 6. Outcome-verified

Ask:

- are we grading the resulting behavior rather than enforcing a specific process?
- can the agent choose its own method as long as the outcome is correct?
- are constraints only there to prevent cheating or preserve the task contract?

Warning signs:

- tool mandates that cannot be verified
- long required procedures instead of outcome requirements
- process scoring masquerading as correctness

## Common Rejection Patterns

Be especially cautious when the task:

- becomes trivial once the honest checked behavior is written into the prompt
- relies on discovering one hidden broken day/file/payload
- is mainly "repair one artifact" rather than implement a broader fix
- is huge in scope and would take far too long even for an expert
- is interesting only because it exploits a model quirk rather than real engineering difficulty
- leaks the answer through visible files or overly direct artifacts
- is labeled `long_context` even though it does not really require at least 50k tokens / roughly 50-150 pages of semantic reading
- is labeled `api_integration` even though it depends on a non-local or external web API
- is described as a UI task even though it is really a backend or service task that would fit ordinary pytest-only validation
- chooses Python as the default implementation language without a good reason
- chooses FastAPI by habit rather than because it materially fits the task

## How to Respond

For each criterion:

1. list positive aspects first
2. list negative aspects second
3. make a judgment for that criterion

Then provide:

- a short restatement of the problem
- a final analysis
- one final decision using the exact decision scale above

## Required Output Template

```text
Problem statement: [re-statement]

Verifiable
[pros]
[cons]
Judgement: {Strong Reject | Reject | Uncertain | Accept | Strong Accept}

Well-specified
[pros]
[cons]
Judgement: {Strong Reject | Reject | Uncertain | Accept | Strong Accept}

Solvable
[pros]
[cons]
Judgement: {Strong Reject | Reject | Uncertain | Accept | Strong Accept}

Difficult
[pros]
[cons]
Judgement: {Strong Reject | Reject | Uncertain | Accept | Strong Accept}

Interesting
[pros]
[cons]
Judgement: {Strong Reject | Reject | Uncertain | Accept | Strong Accept}

Outcome-verified
[pros]
[cons]
Judgement: {Strong Reject | Reject | Uncertain | Accept | Strong Accept}

Final analysis
[analysis here]

Decision: {Strong Reject | Reject | Uncertain | Accept | Strong Accept}
```

## Strict Formatting Requirement

The final line with `Decision:` must match this regex:

```python
re.match(r"\*{0,2}Decision:\*{0,2}\s*\*{0,2}(.+?)\*{0,2}\s*$", line, re.IGNORECASE)
```

Do not use any other final decision wording.

## Final Constraint

Do not provide fix suggestions after the final decision unless the user explicitly asks for them in a separate step. This rubric's job is to evaluate the proposal as presented.
