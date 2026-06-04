# Audit wall clock

Validity windows on credential blobs are evaluated in **GMT** as printed by `openssl x509 -noout -dates`. The comparison instant must come from the wall-clock basis declared in `/app/config/runtime.env` as `TZ_BASE` (currently `UTC`).

Rules:

1. Load `TZ_BASE` from `runtime.env` for every row audit. Do not pass ad hoc timezone literals into the window helper.
2. Convert both `notBefore` and `notAfter` strings to epoch seconds using a **GMT-aware** parser. Treating OpenSSL's `... GMT` timestamps as local `os.time` components skews pre-open and expired classification.
3. Compare epochs with `TZ=${TZ_BASE} date +%s` (without forcing `-u` on the shell clock while overriding `TZ`).

Drift signature: future-validity leaves read `live`, expired leaves read `live`, or both flip together on packs that share the same PEM generator.
