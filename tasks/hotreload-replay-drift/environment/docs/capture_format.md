# Velox capture format

Each file describes one session. Lines are whitespace-separated tokens.

- `session <id>` — session name (example: `session mirror_reload`)
- `frames <n>` — inclusive frame horizon (1..n)
- `reload <frame> <tag>` — optional in-session script boundary (`reload_frame` / `reload_tag` in the parser)
- `body <id> <team> <x> <y> <vx> <vy> <hp> <radius>` — decimal fields use three fractional digits; a whole part of `-0` parses as zero (sign discarded), so `-0.150` encodes like `0.150`
- `original` / `playback` — event sections
- `event <frame> <seq> <unit> <op> <a> <b> <c>` — `push`, `guard`, or `strike` rows
- `end` — closes a section

Event ops map to drift labels when the `original` and `playback` sections disagree on `first_bad_frame`:

- `push` — velocity input; parameter mismatches label as `input`
- `guard` — health input; parameter mismatches label as `input`
- `strike` — target impact; parameter or target mismatches label as `impact`

Classify by diffing per-unit event signatures on that frame (original units first, then playback-only units). See `report_schema.md` for `reason` and `source`.

The probe replays both sections against the same body list and compares digests.
