# Catalog memo 04 — holdout POST envelope

POST `/api/v1/predictions` body:

- `split_id` — must match the active bench split or the service scores zero rows.
- `predictions` — array of `{user_id, item_id, score}` (not `items`).

Before clamping to **[1, 5]**, quantize each score to **quarter-star** granularity: `round(score * 4) / 4`. Full-precision floats inflate rmse on bench-split-a7.

Include every holdout pair from `/api/v1/holdout`.
