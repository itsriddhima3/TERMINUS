# Catalog memo 03 — dwell outcome coupling

## Stable bands

After each `tick`, compare `metric_a`, `metric_b`, and `metric_c` against inclusive band windows stored on the scenario row (`band_*_lo` / `band_*_hi`). All three must be in band simultaneously for the tick to count as **stable**.

## Dwell counter

The session `stable_streak` field is the dwell counter. It increments by one on stable ticks and **resets to zero** when any metric leaves band. It must **not** increment on `set` alone.

## Victory

Victory requires dwell counter **`>= stable_needed`** from the scenario row (SCN-Alpha uses **3**). A single stable tick is insufficient.

## Breach cutoff (loss)

Loss fires when any metric **`>= loss_*`** column from the scenario row (SCN-Alpha breach cutoff **100** per metric). **Do not** compare against band upper bounds (`band_*_hi`) for loss — archive drafts conflated ceiling with breach and caused early loss or missed breaches.
