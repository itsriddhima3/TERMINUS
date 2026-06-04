### Decision
GO — Attempt 1. Java PKI trust auditor with 3MB+ dossier-driven policy, opaque chain/policy/graph fix symbols, milestone split across corpus index, audit JSON, and Graphviz export.

### Metadata
- version: 2
- Task name: java-pki-trust-audit
- Title: PKI Trust Auditor
- Category: security
- Languages: ["java", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context", "tool_specific"]
- Tags: ["java", "pki", "x509", "graphviz", "crl", "bash"]
- Milestones: 3

## Authoring Brief

### Public contract
Maven CLI `/app/bin/trustaudit` with subcommands `corpus`, `policy`, and `graph`. Matrix `/app/data/cases/case_matrix.json` drives nine bench cases (four baseline plus five adversarial: CRL supersession, PEM fork noise, expired intermediate, not-yet-valid leaf, missing issuer link). Outputs: `/app/output/corpus_index.json`, `/app/output/audit_results.json`, `/app/output/trust.dot`, `/app/output/trust.svg`. Normative rules live only in `/app/docs/pki_ops_dossier/part_05.md` (7.4.x policy, 9.2.x diagram) with precedence in `/app/docs/bench_precedence.md`; milestone instructions describe symptoms only.

### Failure topology
Corpus indexing mis-orders chains and mis-binds AKI/SKI; policy layer merges CRLs with wrong `thisUpdate` precedence and loose path-length caps; graph export uses incorrect node palettes. Long-form dossier and decoy modules distract from the three real fix loci.

### Environment shape
Dockerized Maven project under `/app/cli`, PEM corpora and CRLs under `/app/data/`, dossier markdown under `/app/docs/pki_ops_dossier/`, bench scripts under `/app/app/` and `/app/scripts/`.

### Required artifacts
Milestone layout under `tasks/java-pki-trust-audit/steps/milestone_{1,2,3}/` with instructions, tests, solutions; shared `environment/` (20+ files), `task.toml`, `output_contract.toml`.

### Test plan
M1: schema, nine cases, issuer-walk chain shape, AKI/SKI binding, fork/missing-link parse flags. M2: verdict/reason per case including CRL supersession, validity windows at eval_instant, parse_fail on broken walks. M3: digraph structure and annex 9.2 attribute values derived from audit reasons.

### Hardness axes (target ≤20% solve rate)
- **Discover:** 3MB+ dossier; decoy `CrlMergeArchival` + `crl_merge_notes.md`; rules in part_05 annex index and scattered 7.4/9.2 snippets.
- **Synthesize:** parse → policy → graph pipeline; CRL glob per matrix row; eval_instant couples policy checks.
- **Diagnose:** broken parse appends off-walk CNs after a plausible issuer walk; AKI uses wrong extension OID; RevTable compares `Instant.toString` not GeneralizedTime; op_k7 skips intermediate/leaf validity and uses loose path cap.
- **Navigate coupling:** corpus `chain_ok` gates policy `parse_fail`; graph roles depend on policy `reason` strings from dossier.
- **Beyond training:** X.509 AKI/SKI hex binding, CRL thisUpdate supersession, PKIX validity vs eval instant.

### Triviality Ledger
- Lexicographic-only sort without issuer walk fails fork-noise and order tests.
- Issuer walk alone without stripping bundle noise fails pem_fork_noise.
- Legacy CRL note / `CrlMergeArchival` fails dual_crl_supersede and revoked_intermediate.
- Global Graphviz rankdir tweaks do not set role-specific fills from annex 9.2.

### Per-gate Pitfall Inventory
- RC3: tests assert computed verdicts and DOT attribute values, not file existence only.
- RC7: oracle installs multi-file Java fixes across three milestones (>80 LOC substantive).
- CR2: flipping_point splits parse, policy, and graph styling tests.
- GX9: instructions must not enumerate per-case verdict/reason triples; tests remain authoritative.

### Initial Draft Commitments
- `tasks/java-pki-trust-audit/task.toml`
- `tasks/java-pki-trust-audit/output_contract.toml`
- `tasks/java-pki-trust-audit/environment/Dockerfile` and 25+ files under `environment/`
- `tasks/java-pki-trust-audit/steps/milestone_1/{instruction.md,tests/test_m1.py,tests/test.sh,solution/solve1.sh,solution/fixed/*.java}`
- `tasks/java-pki-trust-audit/steps/milestone_2/...`
- `tasks/java-pki-trust-audit/steps/milestone_3/...`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: cli/src/main/java/trust/parse/step_p4.java — symbol: fn_p4 — chain assembly
- path: cli/src/main/java/trust/parse/step_p4.java — symbol: aki_link_ok — SKI/AKI binding check
- path: cli/src/main/java/trust/policy/RevTable.java — symbol: ingest — CRL merge
- path: cli/src/main/java/trust/policy/op_k7.java — symbol: apply — bench policy evaluation
- path: cli/src/main/java/trust/graph/emit/StyleLedger.java — symbol: attrsFor — diagram roles
- path: cli/src/main/java/trust/graph/emit/step_v2.java — symbol: emit — DOT/SVG export

#### flipping_point_contract
- A: parse/step_p4.java — M1 parse tests
- B: policy/RevTable.java + op_k7.java — M2 policy tests
- C: graph/emit/* — M3 graph tests
- concentration_cap: 0.5

#### decoy_manifest
- decoy/CrlStub.java rhymes with CRL merge (archival only)
- decoy/DotTheme.java rhymes with StyleLedger (palette only)

#### code_forbidden_tokens
code_forbidden_tokens: [trust, audit, certificate, certificates, revocation, diagram, diagrams, policy, policies, corpus, anchor, leaf, intermediate, path, valid, reject, expired, revoked, forestgreen, orange, gray, dashed, red, penwidth, peripheries, schema, verdict, reason, chain, matrix, dossier, bench, pem, crl, graphviz, dot, svg]
