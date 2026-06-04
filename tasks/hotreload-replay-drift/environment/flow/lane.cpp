#include "vx/lane.hpp"

#include <algorithm>
#include <tuple>

namespace vx {

std::vector<Event> fold_a(const std::vector<Event>& xs) {
    std::vector<Event> out = xs;
    std::stable_sort(out.begin(), out.end(), [](const Event& a, const Event& b) {
        return std::tie(a.frame, a.seq, a.unit, a.op, a.a, a.b, a.c) <
               std::tie(b.frame, b.seq, b.unit, b.op, b.a, b.b, b.c);
    });
    return out;
}

}  // namespace vx
