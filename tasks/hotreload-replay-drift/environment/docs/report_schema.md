# Drift report schema

The probe writes one JSON object to `/app/output/drift_report.json`.

## summary

- `checked` — number of sessions scanned
- `stable` — sessions where both sides matched every frame
- `drifted` — sessions with any mismatch

## sessions (sorted by `id`)

Each row includes:

- `id` — session name from the capture file
- `status` — `stable` or `drifted`
- `first_bad_frame` — JSON null when stable; otherwise the first 1-based mismatch frame
- `reason` — `none` when stable; otherwise `input`, `impact`, or `state` (see below)
- `source` — empty when stable or when `reason` is `state`; otherwise the unit id for the first mismatch at `first_bad_frame`

### Drift reason at `first_bad_frame`

Compare `original` and `playback` event rows on the mismatch frame. For each unit, merge that unit's rows on the frame into a signature (unit id, op, and args). Scan original-section units first, then playback-only units; the first unit whose signatures differ between sections sets `source`.

- `impact` — that side's differing signature includes a `strike` event
- `input` — the diff is `push`, `guard`, or other non-strike ops only
- `state` — simulation digests disagree at the frame but every unit's event signatures match (`source` stays empty)
- `original_digest` — final digest from the original section replay
- `replay_digest` — final digest from the playback section replay
- `frames` — declared frame horizon from the capture
