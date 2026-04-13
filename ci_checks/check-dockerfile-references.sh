#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ALLOWLISTED_TASKS=(
    # "example-task"
)

is_task_allowlisted() {
    local task_name="$1"

    local allowlisted_task
    for allowlisted_task in "${ALLOWLISTED_TASKS[@]}"; do
        if [ "$task_name" = "$allowlisted_task" ]; then
            return 0
        fi
    done
    return 1
}

if [ $# -eq 0 ]; then
    FILES_TO_CHECK=$(find tasks -type f -name "Dockerfile" 2>/dev/null || true)
else
    FILES_TO_CHECK="$*"
fi

if [ -z "$FILES_TO_CHECK" ]; then
    echo "No Dockerfiles to check"
    exit 0
fi

FAILED=0
for file in $FILES_TO_CHECK; do
    if [ ! -f "$file" ]; then
        echo "File $file does not exist, skipping" >&2
        continue
    fi

    task_dir=$(dirname "$(dirname "$file")")
    task_name=$(basename "$task_dir")

    if is_task_allowlisted "$task_name"; then
        echo -e "${YELLOW}Skipping allowlisted task: $task_name${NC}"
        continue
    fi

    copy_hits=$(grep -nE '^\s*(ADD|COPY)\b.*\b(solution/|tests/)' "$file" || true)
    reserved_hits=$(grep -nE '^\s*(ADD|COPY|WORKDIR|VOLUME)\b.*[[:space:]]/(tests|solution|oracle)(/|$)|^\s*RUN\b.*\b(mkdir|install -d|ln -s|cp|mv|touch)\b.*[[:space:]]/(tests|solution|oracle)(/|$)' "$file" || true)

    if [ -n "$copy_hits" ] || [ -n "$reserved_hits" ]; then
        echo -e "${RED}Error: $file contains forbidden task-answer or reserved-path references${NC}"
        if [ -n "$copy_hits" ]; then
            echo "Problematic solution/tests copy lines:"
            echo "$copy_hits"
        fi
        if [ -n "$reserved_hits" ]; then
            echo "Problematic reserved-path lines:"
            echo "$reserved_hits"
        fi
        FAILED=1
    fi
done

if [ $FAILED -eq 1 ]; then
    echo -e "${RED}Some Dockerfiles contain forbidden task-answer or reserved-path references${NC}"
    echo -e "${YELLOW}Dockerfiles must not copy solution/tests into the image or create /tests, /solution, or /oracle${NC}"
    exit 1
fi

echo -e "${GREEN}All Dockerfiles are clean of forbidden task-answer and reserved-path references${NC}"
