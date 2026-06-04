# Bench policy precedence

When operator notes disagree, apply this order for SHIP-2024-Q1:

1. Live API responses on port 3921 for tariff, FX, and quota flags.
2. `/app/config/bench_policy.toml` for quota uplift and missing-classification exposure.
3. `/app/docs/value_basis.md` for currency amount scaling (wins over legacy duty_rules prose).
4. `/app/docs/duty_rules.md` for underpaid detection and output shapes.
5. Retired annexes under `/app/docs/archive/` are non-authoritative.
