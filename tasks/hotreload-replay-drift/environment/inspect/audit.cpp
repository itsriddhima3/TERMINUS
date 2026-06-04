#include "vx/audit.hpp"

#include "vx/body.hpp"
#include "vx/lane.hpp"

namespace vx {

Row scan_d(const Capture& x) {
    const auto a = fold_a(x.original);
    const auto b = fold_a(x.playback);
    const auto left = step_c(x.units, a, x.frames, x.reload_frame, false);
    const auto right = step_c(x.units, b, x.frames, x.reload_frame, true);

    Row row;
    row.id = x.id;
    row.frames = x.frames;
    row.original_digest = left.final_digest;
    row.replay_digest = right.final_digest;

    if (left.final_digest == right.final_digest) {
        row.status = "stable";
        row.reason = "none";
        row.first_bad_frame = -1;
        row.source = "";
        return row;
    }

    row.status = "drifted";
    row.first_bad_frame = x.frames;
    row.reason = "state";
    row.source = "";
    return row;
}

}  // namespace vx
