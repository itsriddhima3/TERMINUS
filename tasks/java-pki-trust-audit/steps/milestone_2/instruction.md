Policy evaluation should read `/app/output/corpus_index.json` and write `/app/output/audit_results.json` for every bench case. We are seeing incorrect trust decisions when CRL drops supersede each other, paths exceed the bench depth cap, validity relative to the evaluation instant is ignored, and incomplete issuer walks still receive pass/fail `verdict` values instead of a `reason` of parse failure.

The output is a JSON object with top-level `schema_version` (integer `1`) and a `cases` array. Each row carries `case_id`, `verdict`, `reason`, and `chain_cn`. Accepted chains have `verdict: "accept"` and `reason: null`. Rejected chains use `verdict: "reject"` with a reason drawn from the annex: `expired_root`, `revoked_intermediate`, `path_length`, `expired_intermediate`, `not_yet_valid`, `parse_fail`, or `aki_mismatch`. The evaluation instant is taken from the matrix file. Policy runs on the indexed `chain_cn` whenever it is non-empty; only an empty `chain_cn` yields `parse_fail`.

Bench matrix expectations: `valid_chain`, `pem_fork_noise`, and `dual_crl_supersede` → accept with `reason` null; `expired_root` → reject, `expired_root`; `revoked_intermediate` → reject, `revoked_intermediate`; `path_too_deep` → reject, `path_length`; `expired_intermediate` → reject, `expired_intermediate`; `not_yet_valid_leaf` → reject, `not_yet_valid`; `missing_link` → reject, `parse_fail`.

CRL merge and path rules are in the dossier annex (section 7.4), with precedence in `/app/docs/bench_precedence.md`.

When you're done, **signal completion**.
