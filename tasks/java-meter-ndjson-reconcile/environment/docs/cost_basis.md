# Cost basis

`cost_by_site` accumulates interval energy on each device chain:

1. Sort rows by `reading_at`, preserving stream order for ties.
2. Interval kWh = `max(0, corrected_register_kwh[i] - corrected_register_kwh[i-1])` on the same device.
3. Bill that interval at the **destination row's** `rate_cents` (the later stamp), converted with `/100`.
4. Do not skip intervals between duplicate timestamps — both the first and second row at a shared stamp can contribute energy when corrected registers diverge.

Using the origin row's rate or omitting duplicate-stamp intervals under-bills SITE-NORTH after correction events.
