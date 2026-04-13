#!/bin/bash
#
# Fail if task files contain legacy Edition 1 canary strings (no longer used in Edition 2).
#
# Usage:
#   bash ci_checks/check-no-canary.sh
#       — all tasks under tasks/
#   bash ci_checks/check-no-canary.sh tasks/my-task
#       — one task directory (same file set as above, scoped under that path)
#   bash ci_checks/check-no-canary.sh tasks/my-task/instruction.md ...
#       — explicit files only

set -e

LEGACY_PATTERNS=(
    "harbor-canary GUID"
    "terminal-bench-canary"
)

# Same file selection as the default "all tasks" scan, rooted at $1 (directory).
find_task_canary_files() {
    local root="$1"
    find "$root" -type f \( \
        -name "instruction.md" \
        -o -name "milestone_*.md" \
        -o -path "*/solution/*.sh" \
        -o -path "*/environment/Dockerfile" \
        -o -path "*/tests/*.py" \
    \) -print0
}

declare -a FILES_TO_CHECK=()

if [ $# -eq 0 ]; then
    while IFS= read -r -d '' file; do
        FILES_TO_CHECK+=("$file")
    done < <(find_task_canary_files "tasks")
else
    for arg in "$@"; do
        if [ -d "$arg" ]; then
            while IFS= read -r -d '' file; do
                FILES_TO_CHECK+=("$file")
            done < <(find_task_canary_files "$arg")
        elif [ -f "$arg" ]; then
            FILES_TO_CHECK+=("$arg")
        else
            echo "Path $arg does not exist, skipping" >&2
        fi
    done
fi

if [ ${#FILES_TO_CHECK[@]} -eq 0 ]; then
    echo "No files to check"
    exit 0
fi

FAILED=0
for file in "${FILES_TO_CHECK[@]}"; do
    for pattern in "${LEGACY_PATTERNS[@]}"; do
        if grep -q "$pattern" "$file"; then
            echo "Error: $file contains a legacy canary string"
            FAILED=1
            break
        fi
    done
done

if [ $FAILED -eq 1 ]; then
    echo "Some files still contain legacy canary strings"
    exit 1
fi

echo "No legacy canary strings found"
