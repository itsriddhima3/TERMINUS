# Worked bench-split-a7 examples

**Lane ceiling:** 504 training rows at lane width 17 ⇒ response ceiling **30** (not 29 from integer division).

**Quarter star:** raw 3.141592 → 3.25 before clamp.

**Wire byte:** quantized int8 value `-3` transmits as byte `125` (`-3 + 128`).
