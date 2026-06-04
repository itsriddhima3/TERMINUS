# Compaction window

Nightly compaction runs after ingest burst completes. Abrupt power loss during frame consolidation leaves catalogs unreadable on next boot — field reports cite malformed layout errors even when the main file remains on flash.

Simulated abrupt stops are exercised by `/app/bin/datalog audit` against `/app/data/crash_manifest.toml`.
