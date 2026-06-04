# Statutory value basis

Declared amounts in shipment CSV are already in the line's native currency unit.

**JPY rows:** The file stores **whole yen** (not thousands-yen). Apply `jpy_value_basis.scale` from `/app/config/bench_policy.toml` (currently `1.0`) before duty math. The archived thousands-yen divisor (`0.001`) was retired in 2023 and must not be used.

**Other currencies:** Use `declared_value` as printed.

Duty math always converts through `fx_to_usd` after the value basis scale is applied.
