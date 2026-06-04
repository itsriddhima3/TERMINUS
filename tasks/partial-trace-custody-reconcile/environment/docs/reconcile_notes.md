# Reconcile notes

These notes supplement `/app/docs/channel_priority.md` and `/app/docs/bundle_schema.md`. They describe behavior that does not show up in a single channel file.

## Ingest

Every `channels/*.txt` file contributes lines independently. Nothing in ingest should drop a line just because another channel already mentioned the same unit at the same tick with a different verb.

## Same-tick ordering

When rebuilding holder state for one unit, events at the same tick are applied in sighting-before-handoff order. A handoff line updates the active holder for subsequent sightings at that tick; a sighting line compares against the holder established by earlier events at the tick, not the post-handoff holder unless the handoff was already applied.

## Stutter sightings

If a sighting names the holder the unit already occupies, it records observation only and must not emit a movement row.

## Gap rows

Inferred rows bridge holder changes implied by sightings. Do not emit an inferred row for a tick where an explicit handoff line already covers that unit, even when partial channels still show conflicting sightings.

## Proof digest

`ledger_digest` is SHA-256 over the UTF-8 canonical JSON array of ledger objects with `sort_keys` and compact separators. Each object includes `from`, `inferred`, `object`, `tick`, and `to`.
