# Policy precedence

Handbook section **11.2** governs `<unitdate normal="…">` wire spans. Section **11.9** was withdrawn — do not apply two-digit century folding to batch reconciliation output.

Handbook section **8.4** governs dual creator precedence inside a shared `<controlaccess>` block.

Handbook section **12.2** governs LCSH stem extraction before subject authority lookup.

Handbook section **15.7** governs approximate geographic tier selection. Section **18.2** requires the HTTP service to honor client tier parameters on place resolve.

Handbook section **22.1** governs manuscript accession formatting for MS collections and overrides values in `/app/config/bench_policy.toml` for those records.

Handbook section **14.3** does **not** override `bench_policy.toml`; bench defaults apply where 14.3 is silent.

Handbook sections **23.4**, **23.5**, and **23.6** govern compliance bundle completeness, optional geographic linking, and optional subject linking.

Report queue behavior follows `bench_policy.toml` `[report]` unless handbook section 24.1 specifies otherwise for unresolved rows.
