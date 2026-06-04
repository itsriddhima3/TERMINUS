# Annex A0 — Risk score composition (NORMATIVE)

| Rule ID | Severity | Base risk_score | Notes |
| RISK-01 | pass | 15 | Applies when max slot severity is 0 |
| RISK-01 | warn | 45 | Applies when max slot severity is 1 |
| RISK-01 | fail | 88 | Applies when max slot severity is 2 |
| RISK-02 | cite bonus | +12 per entry in cited_rules | After base assignment; cap total at 100 |

Production vector-lane rows that would otherwise warn are elevated to fail per A3-EMB-TIER; base risk for that path remains the warn base unless a slot severity of 2 was already computed.
