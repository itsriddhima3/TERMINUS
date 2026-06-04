### Decision
GO — Attempt 1. C++ EAD parse/link/report pipeline with local Express authority API, 75k-token curator handbook, three coupled milestones, distributed fix surface across ingest/link/policy modules.

### Metadata
- version: 2
- Task name: cpp-ead-authority-reconcile
- Title: EAD Authority Reconciler
- Category: data-processing
- Languages: ["cpp", "javascript", "bash"]
- Difficulty: hard
- Codebase size: small
- Subcategories: ["api_integration", "long_context"]
- Tags: ["cpp", "ead", "xml", "express", "etl", "archival"]
- Milestones: 3

## Authoring Brief

### Public contract
Build `/app/bin/arcctl` (C++ CLI) against sample EAD finding aids and a local Express authority service on port 3000. Batch `ARC-2024-Q2` with collections `UA-0012`, `MS-0456`, `PH-0789`. Subcommands: `parse` writes `/app/var/records.jsonl` and `/app/var/records.csv`; `link` writes `/app/output/linked.json` with creator, subject, and place authority ids; `report` writes `/app/output/compliance.json` and `/app/output/unresolved.jsonl`.

### Failure topology
Parse drops nested personal names, truncates century digits from unitdate spans (withdrawn §11.9 fold still coded), and permutes CSV columns. Link prefers personal over corporate creators, sends full LCSH strings to subject lookup, and approximate places fail because the HTTP service ignores client tier despite correct CLI requests. Report rewrites MS accessions via bench policy against handbook §22.1, treats collections without geogname as place failures, and omits rows from the compliance bundle.

### Drafting guardrails
Symptoms-only milestone instructions; golden authority ids and date spans appear in tests only. Handbook holds normative § references; bench_precedence.md indexes discoverability. Decoys in `decoy/*.cpp` mirror wrong fixes. Place tier bug lives in `api/server.js`, not the C++ client.

### Triviality Ledger
- Fixing date span alone passes UA test but fails MS/PH century assertions — blocked by per-collection date_span tests.
- Corporate-first pick alone passes UA creator but fails subject stem tests — blocked by independent subject assertions.
- Tier-two place fix alone passes Washtenaw but fails if subject strip still broken — cross-milestone coupling via full link pass.

### Per-gate Pitfall Inventory
- RC1: Oracle patches add parse/link/report logic, not deletions.
- RC3: Tests assert computed authority ids and summary counts, not file existence.
- RC6: Instructions describe wrong outputs, not patch sites.
- RC7: Nine patch hunks across nine C++ files exceed 30 LOC substantive delta.
- CR1/CR7: symbol_table names used verbatim; no `ead`/`parse`/`link` function names on fix path.
- GX9: Collection ids UA.12.003, MS-0456, PH.0789 and batch ARC-2024-Q2 grounded in milestone instructions.

### Initial Draft Commitments
- `tasks/cpp-ead-authority-reconcile/task.toml`
- `tasks/cpp-ead-authority-reconcile/output_contract.toml`
- `tasks/cpp-ead-authority-reconcile/environment/**`
- `tasks/cpp-ead-authority-reconcile/steps/milestone_1/**`
- `tasks/cpp-ead-authority-reconcile/steps/milestone_2/**`
- `tasks/cpp-ead-authority-reconcile/steps/milestone_3/**`
- `specs/cpp-ead-authority-reconcile-rubrics.txt`

### Construction manifest (BLOCKING — Step 2b must follow this verbatim)

#### symbol_table
- path: cli/src/ingest/op_scan_x.cpp
  symbol: scan_controlaccess
  kind: function
  signature: scan_controlaccess(xmlNodePtr root, EadFields& out)
  purpose: walk controlaccess names and subjects from EAD root
- path: cli/src/ingest/op_date_y.cpp
  symbol: format_unitdate
  kind: function
  signature: format_unitdate(const std::string& raw)
  purpose: normalize unitdate slash range to hyphen span
- path: cli/src/ingest/op_emit_z.cpp
  symbol: emit_csv_row
  kind: function
  signature: emit_csv_row(const nlohmann::json& row)
  purpose: serialize one CSV data row for parse output
- path: cli/src/net/op_query_a.cpp
  symbol: query_place
  kind: function
  signature: query_place(const std::string& name, bool approx)
  purpose: resolve place authority id via HTTP tier parameter
- path: cli/src/link/op_strip_b.cpp
  symbol: strip_subject_head
  kind: function
  signature: strip_subject_head(const std::string& raw)
  purpose: reduce LCSH string to lookup stem
- path: cli/src/link/op_pick_c.cpp
  symbol: pick_creator_auth
  kind: function
  signature: pick_creator_auth(const std::vector<std::pair<std::string, std::string>>& names)
  purpose: choose one creator authority from controlaccess names
- path: cli/src/policy/op_acc_d.cpp
  symbol: format_accession_candidate
  kind: function
  signature: format_accession_candidate(const std::string& collection_id)
  purpose: derive accession candidate string for validation
- path: cli/src/policy/op_prec_e.cpp
  symbol: apply_accession_precedence
  kind: function
  signature: apply_accession_precedence(const std::string& collection_id)
  purpose: merge handbook and bench accession precedence
- path: cli/src/report/op_queue_f.cpp
  symbol: filter_report_queue
  kind: function
  signature: filter_report_queue(const nlohmann::json& rows)
  purpose: select rows included in compliance bundle

#### flipping_point_contract
locations:
  - id: A
    path: cli/src/ingest/op_scan_x.cpp
    controls_tests: [test_m1_ua_nested_persname_present, test_m1_jsonl_exists_three_records, test_m1_csv_first_column_collection_id]
  - id: B
    path: cli/src/ingest/op_date_y.cpp
    controls_tests: [test_m1_ua_date_span_century, test_m1_ms_date_span, test_m1_ph_date_span]
  - id: C
    path: cli/src/link/op_pick_c.cpp
    controls_tests: [test_m2_ua_corporate_creator_wins, test_m2_ms_creator, test_m2_ph_creator]
  - id: D
    path: cli/src/net/op_query_a.cpp
    controls_tests: [test_m2_ua_approx_place_tier2, test_m2_ph_place_ann_arbor]
  - id: E
    path: cli/src/report/op_queue_f.cpp
    controls_tests: [test_m3_compliance_records_count, test_m3_summary_fully_linked_three, test_m3_unresolved_jsonl_empty]
no_single_location_flips_majority: true
concentration_cap: 0.5

#### decoy_manifest
- path: decoy/XmlStub.cpp
  kind: helper
  rhymes_with: scan_controlaccess
  non_fix_purpose: validates EAD element shape for logging only
- path: decoy/PolicyStub.cpp
  kind: helper
  rhymes_with: filter_report_queue
  non_fix_purpose: counts policy rows for audit summaries without queue filtering

#### code_forbidden_tokens
code_forbidden_tokens: [bench, ships, cpp, arcctl, cli, sample, ead, finding, aids, parse, emit, var, records, jsonl, csv, batch, collections, ua, ms, ph, subcommands, link, output, linked, report, compliance, unresolved, nested, personal, names, controlaccess, century, digits, unitdate, spans, permutes, columns, layout, docs, handbook, chapters, disagree, date, wire, form, precedence, resolves, conflicts, continue, start, scripts, api, sh, authority, service, port, corporate, bodies, win, lists, both, block, today, always, subject, headings, carry, subdivision, text, lookups, miss, approximate, place, never, reach, secondary, fuzzy, tier, describes, repair, signal, completion, command, finish, producing, manuscript, accession, strings, stay, config, bench_policy, toml, suggests, dot, notation, university, archive, qa, materials, unmatched, entities, belong, queue, silently, dropped, bundle, paths, regenerated, reflects, matches, expects, local, three, john, smith, 1950, 1975, 1880, 1895, 1920, 1930, collection, id, title, span, creator, primary, heading, name, corporate, personal, express, etl, archival, xml, node, api, sh, run, write, producing, finish, include, used, when, done, several, today, right, now, vanish, lose, longer, notes, tying, creators, subjects, places, ids, approx, tier2, ms, prefix, dot, form, fully, linked, zero, empty, total, three, pass, fail, count, bundle, retains, all, remain, entity, linked, expected, bench, expects, repair, report, both, output, regenerated]
