### Hardness audit (Step 3b)

Stage: post-oracle

#### A0 hardness axes

| Axis | Verdict | Evidence |
|------|---------|----------|
| Discover | PASS | Fix sites are opaque crate roots (`x7`, `m4`, `q8`); instruction does not name them. Agent must map `insert_lane` / `lookup_lane` / `remove_lane` call graph and distinguish six decoy helpers (`d3`, `k2`, `n1`, `p5`, `t2`, `v9`) that use similar pointer patterns correctly. |
| Synthesize | PASS | Three independent provenance bugs across three crates; partial fix leaves 5–11 of 16 Miri seeds failing. Corpus spans 15 chapters (~120 pages); Chapter 8 rule must be reconciled with red herrings in Chapters 6, 11, 14, 15 and `audit_trail_notes.md`. |
| Diagnose | PASS | Instruction is symptoms-only (release tests pass, Miri matrix fails). Env docs explicitly rule out RNG, drop-order, and repr(C) hypotheses. |
| Navigate coupling | PASS | `bind_q` cap check looks like bounds but validates store level, not `forward.len()`. Fixing one helper does not fix all scenarios. API hash constraint forbids naive safe rewrites at public surface. |
| Reason beyond training | PASS | Requires Rust stacked-borrows / same-allocation provenance reasoning via long-context doc + Miri, not generic “replace unsafe with safe” pattern matching. |

#### Smallest plausible successful patch

Repair three internal helper crates so each raw pointer is derived from the owning `Vec` buffer with length checks, without touching `seqdx` public signatures or `API_HASH`. Superficially sounds small; locating all three formation sites and rejecting decoy/alternate hypotheses is not.

#### Likely editable frontier

- `x7/src/lib.rs` (insert/remove tower slot access)
- `m4/src/lib.rs` (lookup hop traversal)
- `q8/src/lib.rs` (insert cursor resolution)
- Possibly decoy modules if agent misidentifies hot path

#### Grep-collapse resistance

Searching `.add(` or `as_ptr()` hits decoy modules and production helpers alike. Instruction nouns do not grep onto `op_k` / `step_m` / `bind_q` (CR7 PASS). Chapter 8 no longer names skip-list/tower/forward-table failure modes.

#### Residual hardness (10+ sequential steps)

1. Run matrix audit → observe partial/total failure
2. Reproduce individual failing seeds under Miri
3. Trace call graph from `seqdx` lanes to helper crates
4. Read ~120-page corpus (cannot shortcut via single error string)
5. Read audit trail → avoid RNG/drop/layout dead ends
6. Compare decoy helpers vs hot-path helpers within each crate
7. Identify three distinct pointer-formation bugs
8. Apply provenance-safe indexing in all three crates
9. Preserve API hash and compile surface
10. Re-run full 16-seed matrix
11. Emit `audit_report.json` with `checker_clean: true`

#### Collapse verdict: PASS (with WARN justification)

Mechanical gate: 0 FAIL, 3 WARN (GX3 borderline oracle diff, GX7 path literal, RC8 concentration). Residual work is genuine multi-crate Miri debugging with long-context synthesis, not transcription.

#### Platform difficulty estimate

**Hard** — targets ≤20% pass rate via niche tooling (Miri), obscure long-form documentation, non-obvious triple root cause, and decoy-heavy search space.
