# Annex A2 — Regression submission bands (NORMATIVE)

| Rule ID | Slot | Pass | Warn | Fail | Notes |
| A2-REG-03 | rmse_ratio | <= 1.05 | (1.05, 1.12] | > 1.12 | rmse divided by baseline_rmse |
| A2-REG-04 | mae_ratio | <= 1.08 | (1.08, 1.15] | > 1.15 | mae divided by baseline_mae |
| A2-REG-TIER | experimental | multiply pass/warn ceilings by 1.15 | | | Applies to A2-REG-03 and A2-REG-04 |
| A2-REG-TIER | staging | multiply pass/warn ceilings by 1.05 | | | Applies to A2-REG-03 and A2-REG-04; also used for cls cross-lane RMSE sidecar limits |

Overall regression verdict is max severity across slots after tier adjustment.
