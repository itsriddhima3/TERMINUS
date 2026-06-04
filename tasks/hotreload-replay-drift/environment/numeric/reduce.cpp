#include "vx/reduce.hpp"

namespace vx {

double fold_b(const std::vector<double>& xs, bool reverse_lane) {
    if (xs.empty()) {
        return 0.0;
    }
    std::vector<double> lane = xs;
    if (reverse_lane) {
        std::reverse(lane.begin(), lane.end());
    }
    double acc = lane.front();
    for (std::size_t i = 1; i < lane.size(); ++i) {
        acc += lane[i];
    }
    return acc;
}

}  // namespace vx
