# Annex A1 — Classification submission bands (NORMATIVE)

| Rule ID | Slot | Pass | Warn | Fail | Notes |
| A1-CLS-01 | macro_f1 | >= 0.82 | [0.75, 0.82) | < 0.75 | Primary headline metric |
| A1-CLS-02 | ece | <= 0.06 | (0.06, 0.10] | > 0.10 | Calibration slot |
| A1-CLS-DRIFT | population_shift | n/a | n/a | n/a | When population_shift < 0.05 and ece in (0.10, 0.12], cap verdict at warn (not fail) |

Overall classification verdict is the max severity across slots after drift cap.
