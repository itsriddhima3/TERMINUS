# Local reference service

Base URL: `http://127.0.0.1:8080`

- `GET /health` or `GET /actuator/health` → `{ "status": "UP" }`
- `GET /api/v1/readings/stream?meterId=MTR-2024-Q1&cursor=` → `application/x-ndjson` body; empty cursor returns page 0 with header `X-Next-Cursor: page1` when more pages exist; `cursor=page1` returns the final page with no next cursor
- `GET /api/v1/devices/{deviceId}` → device record from the reference catalog (`device_id`, `site_id`, `max_delta_kwh`) or 404
- `GET /api/v1/corrections?meterId=MTR-2024-Q1` → JSON array of correction events (`device_id`, `reading_at`, `delta_kwh`)

Each NDJSON line carries `device_id`, `reading_at` (ISO8601 UTC), `register_kwh`, and `interval_min`.
