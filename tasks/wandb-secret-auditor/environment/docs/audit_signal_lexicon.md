# Audit signal lexicon (internal)

This note codifies operator-facing strings and binding conventions referenced by the security review transcript. Implementations should treat the transcript as authoritative when the two disagree; this file is a quick index.

## SNIPPET_MARK

When redacting exposure snippets for the JSON report, replace the sensitive value with the literal token `<redacted>` (angle brackets). Keep the surrounding context and the exposure marker text (`api_key=` or `token:`) in the snippet; do not substitute bracket-only placeholders such as `[REDACTED]`.

## ALERT_GRANULARITY

Exposure findings must be emitted at log-line granularity: each physical log line that contains an exposure marker (`api_key=` or `token:`) becomes its own `EXPOSED` alert row. Do not collapse an entire log file into a single alert.

## RUN_LIST_ORDER

The top-level `runs` array must be sorted ascending by each run's `id` field from `meta.json`, not by directory name on disk.

## POLICY_BLOCK_SCOPE

Only directives that appear after the `POLICY_TAG` line that is immediately followed by `STATUS: ACTIVE` apply to link prefixes, redaction regexes, approval keys, and nonce format. Later draft blocks (for example tags marked `STATUS: DRAFT`) are retained for history but must not widen allowances.

## APPROVAL_BINDING

Approval proofs use HMAC-SHA256 over UTF-8 bytes. Field order is `scope|run_id|nonce` joined with `|`. The key material is the `APPROVAL_KEY` value from the active policy block.

## NONCE_LEGACY_REJECT

When the active policy declares `NONCE_FMT: NNC-v2:<run>:<8hex>`, any approval whose nonce begins with `NNC-v1:` must be rejected with reason `invalid-nonce` (even if a proof string is present). Legacy-nonce rejection takes precedence over proof verification: do not surface `invalid-proof` for a row whose nonce is already rejectable under this rule.

## PROOF_REJECT

When an approval's nonce is acceptable under the active `NONCE_FMT` but its `proof` does not match the HMAC recomputation defined in `APPROVAL_BINDING`, the row must be rejected with reason `invalid-proof`. This is the only reason code emitted for proof-mismatch failures; do not substitute alternates such as `bad-proof`, `proof-mismatch`, or `invalid-hmac`.

## TRANSCRIPT_DIGEST

`transcript_hash` is SHA-256 over the concatenation of every `*.txt` file in the transcript directory, sorted by filename, with a single `\n` byte inserted between file bodies (no trailing separator after the final file).

## SECONDARY_REPORT_NAME

When comparing transcript-hash sensitivity in tests or tooling, a second output file may be named `report2.json` alongside `report.json`.
