# Annex A3 — Vector-lane submission bands (NORMATIVE)

| Rule ID | Slot | Pass | Warn | Fail | Notes |
| A3-EMB-05 | recall_at_10 | >= 0.71 | [0.65, 0.71) | < 0.65 | Primary retrieval metric |
| A3-EMB-06 | ndcg_at_10 | >= 0.68 | [0.62, 0.68) | < 0.62 | Ranking metric |
| A3-EMB-TIER | production | warn disallowed | | | production tier cannot ship with warn |
| A3-REG-07 | cross_lane | cite required | | | When cls verdict is warn and reg slot in warn band, cited_rules must include A3-REG-07 |

Vector-lane header kind must be `embedding_report` (not `emb_report`).
