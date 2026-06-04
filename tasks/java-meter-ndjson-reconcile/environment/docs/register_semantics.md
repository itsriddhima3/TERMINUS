# Register semantics (AMI cumulative)

Smart-meter NDJSON lines carry **cumulative** register stamps, not interval deltas. Each `register_kwh` is monotonic non-decreasing within a billing period except when a published correction shaves the stamp backward.

Downstream joins must never difference raw registers across devices. Interval energy for cost roll-ups uses consecutive **corrected** stamps on the same `device_id` sorted by `reading_at`, keeping duplicate timestamps in wire order.

When two rows share a stamp, the correction ledger applies to **each** physical row independently — see `/app/docs/correction_ledger.md`.
