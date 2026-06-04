The guard CLI rejects operator bearers that `/resource/echo` still accepts. Fixture negatives under `/app/platform/runtime.json` must fail consistently across local verification, upstream echo, and independent crypto reporting.

With the API running, repair the verification stack and run `guardctl verify`. Write `/app/output/access_report.json` with `fixture_order`, `catalog_size`, `matrix_digest`, `all_pass`, and `checks` rows carrying `case_id`, `accepted`, `local_ok`, `api_ok`, `crypto_ok`, `http_status`, `kid_seen`, `alg_seen`, `iss_seen`, `nbf_seen`, `exp_seen`, `subject`, and `subject_matches` on the passing probe. `fixture_order` follows `fixture_cases` in `/app/platform/runtime.json`. `matrix_digest` is SHA-256 hex over compact JSON of per-row tuples `[case_id, accepted, local_ok, api_ok, crypto_ok, http_status]` in `checks` order. On `valid_session`, `subject` is the operator username and `subject_matches` is true.

Signal completion when the access report is correct.
