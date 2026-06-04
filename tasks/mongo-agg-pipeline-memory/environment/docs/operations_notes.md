# Field operations bulletin

Batch analytics on the telemetry cluster may use disk spill when sort stages exceed RAM budgets. For WK-SPINE ordering and invoke precedence, defer to `/app/docs/bench_precedence.md` and rollup policy chapter 05.

Index maintenance on `events` should precede explain reviews. Rebuilding unrelated collections does not address spine memory aborts.
