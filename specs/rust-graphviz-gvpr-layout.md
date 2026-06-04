### Decision
GO — Attempt 1. Rust Graphviz batch pipeline with long PDF manual, gvpr degree-zero prune, and sparse_scale/sfdp engine binding across three fix loci.

### Metadata
- version: 2
- Task name: rust-graphviz-gvpr-layout
- Title: Graphviz Layout Prune
- Category: scientific-computing
- Languages: ["rust", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["long_context", "tool_specific"]
- Tags: ["rust", "graphviz", "gvpr", "layout", "dot", "bash"]
- Milestones: 0

## Authoring Brief

### Public contract
`/app/bin/g7render batch` reads `/app/data/workload_matrix.json`, writes `/app/output/layout_report.json` and per-workload SVG/DOT under `/app/output/work/`. Normative prune predicate and `sparse_scale`→sfdp binding only in `/app/docs/layout_algorithms_manual.pdf` (section 4.3). Instruction documents wk-compact and wk-plateau accounting fields only.

### Failure topology
Broken baseline skips real gvpr pass (copies raw DOT), uses class=orphan filter, and routes `sparse_scale` through `dot`. Plateau workloads retain 1200 degree-zero islands and stall or emit SVGs still containing `iso_*` ids.

### Environment shape
Rust workspace (`m7desk`, `p4v`, `k9m`, `n2w`), gvpr script, generated PDF manual + chapters, bench docs, decoy gvpr/rs modules, workload matrix JSON.

### Required artifacts
Standard task tree under `tasks/rust-graphviz-gvpr-layout/` with 20+ environment files, `output_contract.toml`, oracle `solve.sh`, pytest verifier.

### Test plan
Schema and matrix coverage; per-workload node accounting; SVG content checks; raw vs pruned DOT; prune_pass arithmetic; bench profile sfdp binding.

### Drafting guardrails
Symptoms-only instruction (no gvpr/sfdp/degree recipe); opaque fix-path symbols; no answer-shaped fixtures; embed expected values in tests only where instruction names them.

### Triviality Ledger
- Label-based `_iso_` deletion from legacy notes fails when placeholders use `iso_*` ids without orphan class.
- Copy-only prune stage passes prune_pass false and leaves 1520 plateau nodes.
- Switching only engine to sfdp without pruning still embeds `iso_*` in SVG.
- Deleting all nodes with class=placeholder would remove nothing (class is placeholder not orphan).

### Per-gate Pitfall Inventory
- RC3: tests assert node counts and SVG/DOT content, not existence-only.
- RC6: instruction names outcomes, not gvpr invocation strings.
- RC7: oracle rewrites gvpr + Rust lane + engine picker (>30 LOC).
- CR2: flipping_point splits gvpr script, stage_a, op_m7.
- GX9: instruction names each asserted workload field value explicitly.

### Initial Draft Commitments
- `tasks/rust-graphviz-gvpr-layout/instruction.md`
- `tasks/rust-graphviz-gvpr-layout/task.toml`
- `tasks/rust-graphviz-gvpr-layout/output_contract.toml`
- `tasks/rust-graphviz-gvpr-layout/environment/Dockerfile` and 60+ files under `environment/`
- `tasks/rust-graphviz-gvpr-layout/tests/{test.sh,test_outputs.py}`
- `tasks/rust-graphviz-gvpr-layout/solution/solve.sh`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: n2w/stage_filters.gvpr — symbol: stage_filters — kind: constant — signature: gvpr script file — purpose: vertex isolation pass body
- path: n2w/stage_a.rs — symbol: run_prune — kind: function — signature: run_prune(script: &Path, in_dot: &Path, out_dot: &Path) -> io::Result<bool> — purpose: invoke gvpr wrapper
- path: k9m/op_m7.rs — symbol: layout_binary — kind: function — signature: layout_binary(profile: &str) -> &'static str — purpose: map profile id to layout binary name
- path: m7desk/src/cmd/render.rs — symbol: run_batch — kind: function — signature: run_batch(matrix: &Path, report: &Path) -> Result<()> — purpose: batch driver orchestration
- path: p4v/op_gen.rs — symbol: emit_dot — kind: function — signature: emit_dot(spec: &WorkloadSpec, out: &Path) -> io::Result<u32> — purpose: raw DOT emission

#### flipping_point_contract
locations:
  - id: A
    path: n2w/stage_filters.gvpr
    controls_tests: [test_plateau_pruned_dot_has_no_isolated_nodes, test_plateau_svg_excludes_isolated_ids, test_wk_plateau_node_accounting]
  - id: B
    path: n2w/stage_a.rs
    controls_tests: [test_prune_pass_not_noop_on_plateau, test_wk_plateau_node_accounting]
  - id: C
    path: k9m/op_m7.rs
    controls_tests: [test_layout_engine_uses_sfdp_binary, test_compact_svg_lists_all_core_nodes]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: decoy/prune_hint.gvpr — kind: module — rhymes_with: stage_filters — non_fix_purpose: archival label filter
- path: decoy/dot_theme.rs — kind: helper — rhymes_with: layout_binary — non_fix_purpose: SVG theme constants

#### code_forbidden_tokens
code_forbidden_tokens: [graph, graphs, layout, layouts, prune, pruned, isolated, plateau, compact, workload, workloads, render, dot, svg, manual, matrix, vertex, vertices, engine, sparse, scale, node, nodes, report, batch, export, service, placeholder, islands]
