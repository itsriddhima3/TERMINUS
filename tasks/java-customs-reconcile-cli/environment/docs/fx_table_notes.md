# FX table semantics

Fixture table stores `fx_to_usd` as a multiplier from the line currency into USD (EUR 1.10 means one euro equals 1.10 USD for duty math).

Some migration notes describe a reciprocal divide step; the enrichment stage should apply the multiplier directly.
