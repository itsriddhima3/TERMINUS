# Catalog memo 05 — wire byte encoding

Signed band coefficients quantize to int8, then transmit as **unsigned wire bytes** via `wire = int8 + 128`. Readers subtract 128 before applying the band scale.

Storing raw int8 cast to uint8 without the offset breaks dequant symmetry between pack write and submit read paths.
