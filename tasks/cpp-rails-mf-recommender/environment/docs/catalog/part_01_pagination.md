# Catalog memo 01 — remote lane pull

Training observations arrive in **lanes** indexed from one (not zero). Each lane response carries a **ceiling** field naming how many lanes exist for the active bench split — client code must adopt the ceiling from the **latest lane response**, not re-derive it from row totals and lane width using truncating division.

The observation vector for each lane lives under the service's canonical array key (see `/app/docs/api_overview.md` — not the withdrawn `rows` alias from archive).

Continue lane walks while the lane index stays at or below the response ceiling. Lane width defaults to the split's `per_page` unless the service overrides it in the response body.
