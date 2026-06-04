# Catalog memo 03 — on-disk pack layout

Magic `RTPK`, version 1 little-endian header:

| Field | Width |
|-------|-------|
| seed | u32 |
| n_users, n_items, n_factors | u32 each |
| global_mean | f32 |
| train digest prefix | 32 ASCII hex bytes from manifest |

Then `bu` (n_users f32), `bi` (n_items f32).

**Latent bands:** for each user row then each item row: one f32 **band scale** (max-abs/127 with floor 1e-6) followed by `n_factors` wire bytes (memo 05). A single shared scale across all bands is a withdrawn archive pattern.

Dequant: `(wire_byte - 128)` as signed int8, multiply by that row's band scale.
