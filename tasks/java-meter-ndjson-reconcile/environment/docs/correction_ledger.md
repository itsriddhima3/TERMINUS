# Correction ledger

`GET /api/v1/corrections` returns additive `delta_kwh` adjustments keyed by (`device_id`, `reading_at`). The delta adjusts the raw cumulative stamp before any interval math:

`corrected_register_kwh = register_kwh + delta_kwh` when a ledger entry exists for that exact key.

Duplicate timestamps (two NDJSON lines with the same stamp) each receive the ledger delta independently. Applying the adjustment only to the first row at a stamp leaves later rows on the wrong cumulative chain and poisons impossible-delta detection on the second row.

Timestamp keys must match the API wire form including the trailing `Z`.
