# Metadata walker policy

Field discovery runs through `walk_q3` in the hub package before sealing. Redaction rules in `/app/config/redaction.toml` match key tokens against immediate mapping keys at the **document root** for each metadata member. Nested sequences (OAuth provider lists, replica node tables, JSON provider arrays) require dotted and indexed field paths in envelope identifiers.

The hub also ships auxiliary counters (`ScanFlatTokens`, `legacy_n0`) used by offline sqlite dump tooling. Those helpers are not on the sealing hot path.

Diagnostic scripts under `/app/lib/` may report line-prefix hits that do not reflect nested redaction coverage.
