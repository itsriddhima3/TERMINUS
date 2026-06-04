# Catalog part 03 — Q1 finalize seal

Handle teardown flows through the **Q1** journal-layer finalize step after P8 merge completes. Field units must:

1. Invoke the directory barrier helper until success or exhaust **barrier_retries** from `/app/config/bench_profiles.toml`.
2. Write the sync stamp named **sync_stamp_name** (non-empty) into the work directory before closing the handle.

Skipping the barrier or leaving a stub stamp satisfies clean-shutdown smoke tests yet fails abrupt-stop recovery: the main file replays but audit dimensions tied to Q1 remain red.

Q1 never substitutes for K2 open class or P8 merge class — partial repairs to one subsystem leave distant invariants failing.
