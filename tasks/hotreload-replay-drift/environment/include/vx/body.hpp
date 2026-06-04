#pragma once

#include <vector>

#include "vx/types.hpp"

namespace vx {

Run step_c(const std::vector<Unit>& xs,
           const std::vector<Event>& ys,
           int z,
           int reload_frame,
           bool playback_lane);

}  // namespace vx
