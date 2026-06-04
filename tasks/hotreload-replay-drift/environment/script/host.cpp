#include "vx/script.hpp"

namespace vx {

int step_a(int frame, int reload_frame, bool playback_lane) {
    if (reload_frame < 0) {
        return 0;
    }
    if (frame < reload_frame) {
        return 0;
    }
    if (playback_lane && frame >= reload_frame) {
        return 1;
    }
    return 0;
}

}  // namespace vx
