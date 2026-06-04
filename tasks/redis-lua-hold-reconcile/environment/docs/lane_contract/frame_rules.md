# Frame rules (revision B2)

## Observation frame

Host-side tally read immediately before a commit frame is scheduled. Used to reject requests that obviously exceed visible stock without invoking the script engine.

## Commit frame

Server-side script invocation against a bound slot key. Each commit frame executes atomically on the server. Atomicity applies to the script invocation itself, not to any earlier host read in the same grant attempt.

## Parallel lanes

Audit scenarios mix solo and multi-worker lanes. Compliance probes record whether observation forwarding is active and whether worker slot binding matches catalog seeds. Scenario rows record overshoot flags, grant totals, remaining counts, and attempt counts.

## Probe scripts

Registry-listed probe scripts are read-only and run outside the grant hot path.
