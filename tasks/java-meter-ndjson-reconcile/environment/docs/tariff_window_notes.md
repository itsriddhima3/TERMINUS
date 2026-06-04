# Tariff window notes

`/app/data/tariffs.csv` columns: `site_id`, `window_start`, `window_end`, `rate_cents` (clock times HH:mm, site-local).

A reading's `rate_cents` comes from the row whose `site_id` matches the device catalog and whose window contains the reading clock time. The window end is **exclusive**: a reading at exactly `window_end` belongs to the next window, not the current one.

Device catalog join uses `device_id` from readings against `device_id` in `/app/data/devices.csv` to obtain `site_id` and `max_delta_kwh_per_interval`.
