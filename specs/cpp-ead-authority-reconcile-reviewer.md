### Hardness axes (post-hardening)

| Axis | How the task satisfies it |
|------|---------------------------|
| **Discover** | Normative rules live in 75k-token handbook (§8.4, §11.2/11.9, §12.2, §15.7, §18.2, §22.1, §23.4–24.1) and `/app/docs/bench_precedence.md`; instructions state symptoms only. |
| **Synthesize** | Three-stage C++ pipeline + Express API + TOML precedence + EAD XML + CSV/JSONL/report artifacts must align. |
| **Diagnose** | Place tier failure is server-side (`api/server.js`) while client sends correct tier; decoys mirror wrong fixes in `decoy/*.cpp`. |
| **Navigate coupling** | Parse defects poison link; link defects poison report; MS accession needs handbook §22.1 over `bench_policy.toml`; optional geo rule (§23.5) affects fully-linked counts. |
| **Reason beyond training** | EAD archival metadata, LCSH `--` stems, accession prefix families, withdrawn vs active handbook sections. |

### Sequential reasoning depth (10+ steps)

1. Run parse and inspect JSONL/CSV vs layout doc  
2. Locate nested-name drop in ingest scan path  
3. Find century truncation vs handbook §11.2 / withdrawn §11.9 via precedence doc  
4. Fix CSV column order from layout spec  
5. Start authority API and run link  
6. Trace creator precedence against handbook §8.4 (decoy `LinkStub` misleads)  
7. Trace LCSH subdivision failures to stem strip (decoy `SubjectStub` misleads)  
8. Observe approx place failure despite client tier — probe API directly  
9. Read handbook §18.2 and fix server tier routing, not client  
10. Run report; trace MS accession MSS rewrite through policy chain vs §22.1  
11. Apply optional geographic rule so MS without geogname is not a false unresolved  
12. Fix compliance bundle filter dropping linked rows (§23.4 / §24.1)  

### Residual hardness after honest prompt

Instructions no longer enumerate authority ids or date spans. Expected values remain test-only. Agent must read handbook sections indexed in `bench_precedence.md`, distinguish withdrawn §11.9 from active §11.2, and diagnose client/server split for place tier.

### Naming-pass record

Test names audited: test_m1_ua_jsonl_dual_creators_corp_before_pers, test_m1_ua_csv_title_second_column, test_m2_ua_corporate_precedence_over_resolvable_personal, test_m2_batch_accession_and_subjects_reconcile, test_m2_place_api_honors_tier_two_query, test_m3_compliance_records_mirror_linked_auth_ids, test_m3_ms_optional_geographic_still_fully_linked

Concentration math: total 37 tests; max location share 5/37 = 0.135; cap 0.5 PASS
