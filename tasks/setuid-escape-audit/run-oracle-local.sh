#!/bin/bash
# Run oracle (solution + verifier) in one container to see actual errors.
# Usage (from repo root): bash tasks/setuid-escape-audit/run-oracle-local.sh
set -e
TASK_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TASK_DIR/../.." && pwd)"
cd "$REPO_ROOT"
echo "Building image (context = environment/)..."
docker build -t setuid-oracle-local -f "$TASK_DIR/environment/Dockerfile" "$TASK_DIR/environment"
echo "Running solution then verifier..."
docker run --rm \
  -v "$TASK_DIR/solution:/solution:ro" \
  -v "$TASK_DIR/tests:/tests:ro" \
  setuid-oracle-local bash -c '
    set -e
    mkdir -p /app /logs/verifier
    echo "=== Running solve.sh ==="
    bash /solution/solve.sh
    echo "=== Running test.sh ==="
    bash /tests/test.sh
    echo "=== Reward ==="
    cat /logs/verifier/reward.txt
  '
