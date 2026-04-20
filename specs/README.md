# Specs Working Notes

The `specs/` folder is a working directory for Step 2 validation artifacts. Files here are reviewed during authoring and are not part of the submitted task package.

## Split spec contract

Each saved Step 2 spec in `specs/<task-name>.md` should contain two distinct sections:

1. `Authoring Brief`
2. `Reviewer Appendix`

The split is intentional:

- `Authoring Brief` is the only section Step 2b should use when drafting task files.
- `Reviewer Appendix` is for human review only. It may include frontier analysis, exhaustive file inventory ideas, oracle notes, and collapse-audit detail that would over-shape drafting if fed back into Step 2b.

## What belongs in each section

`Authoring Brief` should describe:

- The public contract the eventual `instruction.md` and tests must enforce
- The failure topology: symptom clusters, invariants, and interacting subsystems that make the task hard
- The environment shape at a component level, not an exhaustive file-by-file scaffold
- Required artifacts and test intent

`Reviewer Appendix` may describe:

- The implementation plan in more concrete terms
- A proposed exhaustive file tree or component inventory
- Oracle notes
- Collapse-audit analysis and per-test feasibility review

## Other generated files

The validation loop may also create:

- `specs/<task-name>-candidate-N.md` for plateau candidates
- `specs/<task-name>-attempt-N-evidence.json` for structured evidence
- `specs/<task-name>-validation-log.md` for attempt history

These are reviewer artifacts. They are not drafting inputs for Step 2b.
