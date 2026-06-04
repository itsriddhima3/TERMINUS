# Runtime notes

Velox integrates a lightweight script host that can swap gameplay modules mid-session. Script boundaries are recorded in captures so offline replay can reproduce the same module schedule.

Neighbor soft forces are accumulated each frame before positional integration. The engine keeps unit state in fixed-point millis for positions and velocities.
