# Catalog memo 04 — session archive round-trip

## Active slot

Slot `active` holds live tick index, the three metrics, dwell counter (`stable_streak`), and outcome flags.

## Named slots

`save <name>` copies the active row into a named slot. `load <name>` restores it.

Required round-trip fields:

- tick index
- metric triple
- dwell counter (must not be zeroed on save when active streak is non-zero)
- component levels for all nine cells (persisted via `slot_levels` snapshot)

## SQLite buffering note

When archiving levels, read all component rows into memory before writing `slot_levels` rows. Interleaving a open read cursor with writes on the same connection can surface `database is locked` and silently truncate streak or level snapshots.
