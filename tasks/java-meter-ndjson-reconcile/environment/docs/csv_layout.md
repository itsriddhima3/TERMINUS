# Local CSV layout

`/app/data/devices.csv` header:

`device_id,site_id,max_delta_kwh_per_interval`

`/app/data/tariffs.csv` header:

`site_id,window_start,window_end,rate_cents`

Normalize joins devices on `device_id` and resolves tariffs per `site_id` and reading clock time. Persisted normalized JSON uses keys `meter_id` and `readings` with enriched rows.
