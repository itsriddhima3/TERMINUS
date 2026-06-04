#!/bin/bash
set -euo pipefail
MATRIX=/app/data/cases/case_matrix.json
/app/bin/trustaudit corpus --matrix "$MATRIX"
/app/bin/trustaudit policy --matrix "$MATRIX" --corpus /app/output/corpus_index.json
/app/bin/trustaudit graph --audit /app/output/audit_results.json
