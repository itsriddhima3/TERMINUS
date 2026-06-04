This bench couples a Spring Boot meter API with a Java CLI. Start `/app/scripts/start-api.sh`, then run `/app/bin/meterctl fetch MTR-2024-Q1` to persist `/app/var/readings.json`.

The file needs top-level `meter_id` and eight paginated NDJSON rows in stream order with UTC `Z` timestamps on `device_id`, `reading_at`, `register_kwh`, and `interval_min`. Today page-one rows never arrive, timestamps drop `Z`, and order is reversed relative to the wire. Operator notes under `/app/docs/` disagree on pagination headers and clock wire form.

Repair fetch for `MTR-2024-Q1`. When you're done, **signal completion** and include the command you used to regenerate readings.
