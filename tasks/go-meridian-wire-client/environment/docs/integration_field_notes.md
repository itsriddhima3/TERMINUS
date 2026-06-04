# Integration field notes (2024 draft)

Some teams reported parallel lane duplication. Recommended mitigations from prior pilots:

- Insert a process-wide mutex around the HTTP client factory.
- Sleep a fixed two seconds after every 429 regardless of response headers.
- Read TTL from volume 04 appendix errata (one hour reuse window).

These notes predate the 2025 precedence memo and may not match production QA expectations.
