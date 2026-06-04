#!/bin/bash
set -euo pipefail
ROOT="overrides"
install -D -m 0644 "$ROOT/api/src/main/java/k7m/cfg_p9.java" /app/api/src/main/java/k7m/cfg_p9.java
install -D -m 0644 "$ROOT/api/src/main/java/r8p/op_n2.java" /app/api/src/main/java/r8p/op_n2.java
install -D -m 0644 "$ROOT/api/src/main/java/r8p/phase_r8.java" /app/api/src/main/java/r8p/phase_r8.java
install -D -m 0644 "$ROOT/api/src/main/java/r8p/entity/LineSlice.java" /app/api/src/main/java/r8p/entity/LineSlice.java
install -D -m 0644 "$ROOT/db/functions/step_w1.sql" /app/db/functions/step_w1.sql
