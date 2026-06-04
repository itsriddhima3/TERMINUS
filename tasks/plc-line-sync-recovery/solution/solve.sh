#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/usr/local/go/bin:/app/bin:${PATH}"
export CGO_ENABLED=1
cd /app

cat > /app/sync_core/src/lib.rs <<'EOF'
use std::ffi::CStr;
use std::os::raw::{c_char, c_uint};

fn slot_tag(slot: u32, answer: &str) -> u16 {
    let mut sum: u32 = 0;
    for b in answer.bytes() {
        sum = sum.wrapping_add(u32::from(b));
    }
    ((sum ^ slot) & 0xFFFF) as u16
}

fn fold_min(values: &[u32]) -> u32 {
    values.iter().copied().min().unwrap_or(0)
}

#[no_mangle]
pub extern "C" fn op_g(
    anchor: *const c_char,
    stamp: *const c_char,
    slot: c_uint,
    answer: *const c_char,
    stored: u16,
) -> bool {
    if anchor.is_null() || stamp.is_null() || answer.is_null() {
        return false;
    }
    let anchor = unsafe { CStr::from_ptr(anchor).to_str().unwrap_or("") };
    let stamp = unsafe { CStr::from_ptr(stamp).to_str().unwrap_or("") };
    let answer = unsafe { CStr::from_ptr(answer).to_str().unwrap_or("") };
    if stamp != anchor {
        return false;
    }
    slot_tag(slot, answer) == stored
}

#[no_mangle]
pub extern "C" fn op_m(values: *const c_uint, count: usize) -> c_uint {
    if values.is_null() || count == 0 {
        return 0;
    }
    let slice = unsafe { std::slice::from_raw_parts(values, count) };
    fold_min(slice)
}
EOF

cat > /app/pkg/replicount/op_q.go <<'EOF'
package replicount

func quorumMet(count int, need int) bool {
	if need <= 0 {
		return false
	}
	if count < 0 {
		return false
	}
	return count >= need
}

// OpQ decides whether enough replicas reported the same payload group.
func OpQ(replicaCount int, need int) bool {
	return quorumMet(replicaCount, need)
}
EOF

cat > /app/pkg/timenorm/op_t.go <<'EOF'
package timenorm

func normalizeWall(wall int64, offset int64) int64 {
	return wall - offset
}

// OpT adjusts wall time for drift comparisons.
func OpT(wall int64, offset int64) int64 {
	return normalizeWall(wall, offset)
}
EOF

cat > /app/pkg/markfold/op_w.go <<'EOF'
package markfold

func minMark(marks []int64) int64 {
	if len(marks) == 0 {
		return 0
	}
	best := marks[0]
	for _, m := range marks[1:] {
		if m < best {
			best = m
		}
	}
	return best
}

// OpW folds per-member freeze marks into one replay watermark.
func OpW(marks []int64) int64 {
	return minMark(marks)
}
EOF

bash /app/scripts/build.sh

rm -f /app/output/sync_report.json
mkdir -p /app/output
TB_LINE_FIXTURE=1 /app/bin/line_audit
test -s /app/output/sync_report.json

GOFLAGS=-mod=mod go test ./...
