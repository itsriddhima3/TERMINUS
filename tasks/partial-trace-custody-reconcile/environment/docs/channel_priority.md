# Channel priority

Each observation file under a pack's `channels/` directory is named after its channel id (stem of the filename). `/app/config/channel_ranks.json` maps channel ids to integer ranks (for example `north` above `gate`, with `yard` and `quay` tied at the lowest rank); higher rank wins when two channels report different holders for the same unit at the same tick.

Sightings use the `see` verb; explicit handoffs use `xfer`. A handoff line is authoritative for that tick and does not count as a contradiction against sighting lines at the same tick — the `contradiction_resolved` counter must skip that `(tick, object)` pair even when channels still disagree on sightings.

When ranks tie, the channel id that sorts later lexicographically wins.

Initial holders come from the pack `meta.json` `initial_holders` map before any channel lines are applied.
