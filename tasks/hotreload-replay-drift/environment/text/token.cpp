#include "vx/token.hpp"

#include <sstream>

namespace vx {

std::string fold_d(const std::map<std::string, Unit>& xs) {
    std::ostringstream out;
    bool first = true;
    for (const auto& [id, u] : xs) {
        if (!first) {
            out << '|';
        }
        first = false;
        const long long hp = u.hp < 0 ? 0 : u.hp;
        out << id << ':' << u.team << ':' << u.x << ',' << u.y << ':' << u.vx << ',' << u.vy
            << ':' << hp;
    }
    return out.str();
}

}  // namespace vx
