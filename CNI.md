# Currently Not Implementing (CNI)

This file tracks ideas that came out of reviews, retros, or task postmortems
but that we have deliberately **not** implemented. Each entry names the
problem the idea would solve, the shape of the proposed fix, and the reason
it is on hold. Add new entries at the top. Move an entry out of this file
when it gets implemented, and delete the entry (don't just strike it through).

---

## Platform-agnostic hard-task pattern library

**Problem it would solve.** Some hard-task design patterns reliably produce
genuine residual difficulty (systemic coupling, symptoms-only instructions,
invariant spans across files). Authors have to rediscover them each time.
A pattern library would compress institutional knowledge into "shapes" of
hard tasks — e.g., "local fix breaks distant invariant," "cross-module
vocabulary mismatch," "recovery-state inconsistency across restart,"
"version-skew between writer and reader."

**Shape of the proposal.** A `patterns/` directory with one file per
pattern, each containing: the invariant structure, why it's hard, a
skeleton of environment/tests, an exemplar task, and an anti-pattern
(what collapse looks like). `collapse_check.py` or a sibling could match
new submissions against these shapes and flag "this is pattern X; confirm
the coupling is genuinely present."

**Why on hold.** Three reasons:

1. **It may kill variation.** The whole point of hard-task diversity is
   that no two tasks should feel like refills of the same template. A
   pattern library could very easily become a template library in
   practice, with authors picking the nearest shape and filling it in.
   That's the RC6 `spec-complete` failure at the repo level rather than
   the task level.

2. **The patterns are model-family-specific and drift.** What's "hard
   coupling" for Claude 4.6 may be easy for Claude 4.7 or GPT-5.3. Any
   static library of hard shapes has a decay half-life measured in model
   releases. We'd end up maintaining it against moving targets.

3. **The existing hardness axes already do this job.** `idea-validation.mdc`
   already enumerates 5 hardness axes, 20 anti-trivialization checks, and
   6 rubric axes. If we find that authors consistently fail the same axis
   (say, "Navigate coupling"), the right move is to tighten that axis's
   mechanical enforcement, not to add a new layer. A pattern library is
   a second abstraction for the same concept.

**What would move this off the back burner.** Evidence that 3+ recently-
rejected tasks failed along the *same* structural dimension that a specific
pattern would have caught at idea-validation time. Until we have that
evidence, adding the layer is premature standardization.

---

## Instruction-diversity repo-wide lint

**Problem it would solve.** Rules already say "vary the style across tasks,"
but no mechanical check verifies it. A reviewer approving five tasks in
sequence can drift into a house style without noticing. If every task opens
with "Repair the X under /app/src." and ends with a schema block, the
agent learns to pattern-match those shapes and skip the hard reasoning.

**Shape of the proposal.** A script that reads every `instruction.md` in
`Task_Ready_To_Submit/` and computes diversity metrics: length distribution,
structural features (headers vs. prose vs. bullets), opening-sentence
similarity (sentence-embedding cosine or token-level Jaccard), ending-line
patterns. Flags the repo if the set collapses to a narrow mode.

**Why on hold.** Diversity is hard to measure without either (a) an LLM
call, which makes the check non-deterministic, or (b) a hand-crafted
feature set that's brittle and gameable. A sentence-embedding approach
needs an embedding model; a token-level approach has false positives on
incidental shared vocabulary. Neither shape is clean enough to ship as
a mandatory gate. Covered softly by `run_static_checks.py --only
instruction_test_vocabulary` which at least forces the instruction to
carry the vocabulary tests use, and by the strengthened humanization
language in `.cursor/rules/task-creation.mdc` that calls out template
drift explicitly.

**What would move this off the back burner.** A concrete case where two
or more approved tasks were found to share enough structural DNA that
an agent could have solved one from the other's pattern, plus a
diversity metric whose false-positive rate on hand-varied tasks is
under 10%.

---

## Per-model calibration heuristics (Claude-specific or GPT-specific)

**Problem it would solve.** A task rated "hard" because it scored 0/5 on
Claude but 4/5 on GPT-5.2 isn't really hard — it's hard-for-one-model.
Conversely, tasks that Claude passes but GPT fails are currently shipped
under the same "hard" label, but they're measurably narrower. A per-model
calibration heuristic would flag these imbalances and force authors to
diversify the failure mode.

**Shape of the proposal.** After post-upload evaluation data is available, compare per-model
pass rates. Flag any task where `abs(pass_rate_claude - pass_rate_gpt5) > 0.5`.
Optionally, maintain a rolling metric per model and reject tasks whose
inclusion would skew the benchmark's overall Claude-vs-GPT discrimination
beyond a target threshold.

**Why on hold.** This is adversarial calibration against a moving target.
Any rule tuned to widen Claude-GPT gaps today will stop working on the
next model release. It also creates a perverse incentive: authors would
start optimizing for "finds a model asymmetry" rather than "produces
genuine residual difficulty." The existing hardness axes are the
durable answer — a task that genuinely requires Discover + Synthesize +
Diagnose + Navigate-coupling + Reason-beyond-training will be hard for
all frontier models, and will stay hard across model releases.

**What would move this off the back burner.** Evidence that the
benchmark's discrimination power is degrading specifically because
approved tasks cluster in a model-asymmetric region of the space, AND
a proposed metric whose false-positive rate on genuinely-hard tasks is
under 20%. Neither is established. For now, strengthen the hardness
axes rather than targeting specific models.

---

## Static oracle-tests parity check

**Problem it would solve.** At least one shipped task (`rollback-replay-
divergence`) contained a test that failed 10/10 under the oracle itself
— the test's assumption about what a partial-fix profile should produce
was wrong, so even a complete fix couldn't satisfy it. `verifier_health.py`
catches this empirically via its `repeat_oracle` check, but only if the
reviewer actually runs it before approving. There's no static check.

**Shape of the proposal.** A check that inspects `tests/test_outputs.py`
for any `pytest.mark.xfail` or any test that calls a build helper with
kwargs differing from the oracle's build profile, and requires either
(a) an explicit xfail marker with a reason, or (b) an inline comment
noting "partial-fix inversion: expected to pass with full oracle."
Cross-reference with `solution/solve.sh` to confirm the oracle's profile
actually produces the expected pass.

**Why on hold.** The empirical gate (`verifier_health.py`'s `repeat_oracle`
check, which `approve_task.py` requires) already catches this. Adding a
static check would duplicate the empirical one and could fire false
positives on legitimate inversion tests. The right leverage is instead
in the review doc: we added "Every shipped test must pass under the
oracle" as an explicit checklist item in `review-and-submit.mdc` with
a note that `verifier_health.py` is the mechanical check.

**What would move this off the back burner.** Evidence that reviewers
are shipping tasks without running `verifier_health.py`, such that a
static pre-check would actually prevent the same class of failure. If
that happens, build the check as an AST-level inspector before
`approve_task.py` consumes the health report.

---
