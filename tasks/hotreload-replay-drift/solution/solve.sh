#!/bin/bash
set -euo pipefail

# Read the bundled docs for capture layout, drift labels, and runtime behavior.
cat /app/docs/capture_format.md
cat /app/docs/report_schema.md
cat /app/docs/runtime_notes.md

# Locate replay and audit entry points referenced by the report contract.
grep -Rn 'scan_d\|step_a\|fold_b\|fold_m\|playback_lane\|reverse_lane' \
    /app/inspect /app/script /app/numeric /app/arena /app/src

# Read decimal folding — capture_format notes that `-0.xxx` drops the sign on purpose.
grep -n 'fold_m' /app/numeric/math.cpp /app/include/vx/math.hpp
sed -n '1,35p' /app/numeric/math.cpp

# Read the three modules that diverge original vs playback replay.
echo '--- reduce.cpp (neighbor soft-force fold) ---'
cat /app/numeric/reduce.cpp
echo '--- host.cpp (reload epoch gate) ---'
cat /app/script/host.cpp
echo '--- audit.cpp (drift scan) ---'
cat /app/inspect/audit.cpp

# reduce.cpp: fold_b reverses the neighbor list when reverse_lane is true, but
# runtime_notes says soft forces accumulate in stable unit order each frame.
cat > /app/numeric/reduce.cpp <<'EOF'
#include "vx/reduce.hpp"

namespace vx {

double fold_b(const std::vector<double>& xs, bool reverse_lane) {
    (void)reverse_lane;
    if (xs.empty()) {
        return 0.0;
    }
    double acc = xs.front();
    for (std::size_t i = 1; i < xs.size(); ++i) {
        acc += xs[i];
    }
    return acc;
}

}  // namespace vx
EOF

# host.cpp: step_a returns a different epoch after reload on playback only; reload
# rows must not change simulation rules between original and playback lanes.
cat > /app/script/host.cpp <<'EOF'
#include "vx/script.hpp"

namespace vx {

int step_a(int frame, int reload_frame, bool playback_lane) {
    (void)playback_lane;
    if (reload_frame < 0 || frame < reload_frame) {
        return 0;
    }
    return 1;
}

}  // namespace vx
EOF

# audit.cpp: scan_d must replay both lanes with the same rules, compare per-frame
# digests for first_bad_frame, and classify reason/source from event diffs.
cat > /app/inspect/audit.cpp <<'EOF'
#include "vx/audit.hpp"

#include <map>
#include <string>

#include "vx/body.hpp"
#include "vx/lane.hpp"

namespace vx {
namespace {

std::string sig(const Event& e) {
    return e.unit + ":" + e.op + ":" + e.a + ":" + e.b + ":" + e.c;
}

std::string classify(const std::vector<Event>& a,
                     const std::vector<Event>& b,
                     int frame,
                     std::string& source) {
    std::map<std::string, std::string> left;
    std::map<std::string, std::string> right;
    for (const auto& e : a) {
        if (e.frame == frame) {
            left[e.unit] += sig(e) + ";";
        }
    }
    for (const auto& e : b) {
        if (e.frame == frame) {
            right[e.unit] += sig(e) + ";";
        }
    }
    for (const auto& [unit, text] : left) {
        if (right[unit] != text) {
            source = unit;
            return text.find(":strike:") != std::string::npos ? "impact" : "input";
        }
    }
    for (const auto& [unit, text] : right) {
        if (left[unit] != text) {
            source = unit;
            return text.find(":strike:") != std::string::npos ? "impact" : "input";
        }
    }
    source.clear();
    return "state";
}

}  // namespace

Row scan_d(const Capture& x) {
    const auto a = fold_a(x.original);
    const auto b = fold_a(x.playback);
    const auto left = step_c(x.units, a, x.frames, x.reload_frame, false);
    const auto right = step_c(x.units, b, x.frames, x.reload_frame, false);

    Row row;
    row.id = x.id;
    row.frames = x.frames;
    row.original_digest = left.final_digest;
    row.replay_digest = right.final_digest;

    const std::size_t n = std::min(left.snapshots.size(), right.snapshots.size());
    int first = -1;
    for (std::size_t i = 0; i < n; ++i) {
        if (left.snapshots[i].digest != right.snapshots[i].digest) {
            first = left.snapshots[i].frame;
            break;
        }
    }

    if (first < 0) {
        row.status = "stable";
        row.reason = "none";
        row.first_bad_frame = -1;
        row.source = "";
        return row;
    }

    row.status = "drifted";
    row.first_bad_frame = first;
    row.reason = classify(a, b, first, row.source);
    return row;
}

}  // namespace vx
EOF

cmake -S /app -B /app/build
cmake --build /app/build --target velox_probe --parallel 2
