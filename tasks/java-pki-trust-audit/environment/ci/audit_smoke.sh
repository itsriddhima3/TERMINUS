#!/bin/bash
set -euo pipefail
test -x /app/bin/trustaudit
/app/bin/trustaudit corpus --matrix /app/data/cases/case_matrix.json
test -f /app/output/corpus_index.json
