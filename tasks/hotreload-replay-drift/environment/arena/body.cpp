#include "vx/body.hpp"

#include <algorithm>
#include <cmath>
#include <map>
#include <vector>

#include "vx/math.hpp"
#include "vx/reduce.hpp"
#include "vx/script.hpp"
#include "vx/token.hpp"

namespace vx {
namespace {

bool ok_a(const Unit& u) {
    return u.hp > 0;
}

long long sq(long long x) {
    return x * x;
}

bool ok_b(const Unit& a, const Unit& b, long long extra) {
    const long long dx = a.x - b.x;
    const long long dy = a.y - b.y;
    const long long r = a.radius + b.radius + extra;
    return sq(dx) + sq(dy) <= sq(r);
}

void clamp(Unit& u) {
    if (u.hp < 0) {
        u.hp = 0;
    }
}

void apply_soft(std::map<std::string, Unit>& world, int epoch) {
    std::vector<std::string> ids;
    for (const auto& [id, _] : world) {
        ids.push_back(id);
    }
    std::sort(ids.begin(), ids.end());

    const bool reverse_lane = epoch > 0;
    for (const auto& id : ids) {
        auto& u = world[id];
        if (!ok_a(u)) {
            continue;
        }
        std::vector<double> parts;
        for (const auto& oid : ids) {
            if (oid == id) {
                continue;
            }
            const auto& o = world.at(oid);
            if (!ok_a(o)) {
                continue;
            }
            const double dx = static_cast<double>(o.x - u.x);
            const double dy = static_cast<double>(o.y - u.y);
            const double dist = std::sqrt(dx * dx + dy * dy) + 1.0;
            parts.push_back((dx / dist) * 0.001 + (dy / dist) * 0.0007);
        }
        const double impulse = fold_b(parts, reverse_lane);
        u.vx += static_cast<long long>(impulse * 1000.0);
        u.vy += static_cast<long long>(impulse * 500.0);
    }
}

}  // namespace

Run step_c(const std::vector<Unit>& xs,
           const std::vector<Event>& ys,
           int z,
           int reload_frame,
           bool playback_lane) {
    std::map<std::string, Unit> world;
    for (const auto& u : xs) {
        world[u.id] = u;
    }

    Run out;
    for (int frame = 1; frame <= z; ++frame) {
        const int epoch = step_a(frame, reload_frame, playback_lane);

        for (const auto& e : ys) {
            if (e.frame != frame) {
                continue;
            }
            auto it = world.find(e.unit);
            if (it == world.end() || !ok_a(it->second)) {
                continue;
            }
            if (e.op == "push") {
                it->second.vx += fold_m(e.a);
                it->second.vy += fold_m(e.b);
            } else if (e.op == "guard") {
                it->second.hp += fold_m(e.a);
            } else if (e.op == "strike") {
                auto jt = world.find(e.a);
                if (jt != world.end() && ok_a(jt->second) && ok_b(it->second, jt->second, 1500)) {
                    jt->second.hp -= fold_m(e.b);
                    clamp(jt->second);
                }
            }
        }

        apply_soft(world, epoch);

        std::vector<std::string> ids;
        for (const auto& [id, _] : world) {
            ids.push_back(id);
        }
        std::sort(ids.begin(), ids.end());
        for (const auto& id : ids) {
            auto& u = world[id];
            if (ok_a(u)) {
                u.x += u.vx;
                u.y += u.vy;
            }
        }

        for (std::size_t i = 0; i < ids.size(); ++i) {
            for (std::size_t j = i + 1; j < ids.size(); ++j) {
                auto& a = world[ids[i]];
                auto& b = world[ids[j]];
                if (ok_a(a) && ok_a(b) && a.team != b.team && ok_b(a, b, 0)) {
                    a.hp -= 1000;
                    b.hp -= 1000;
                    a.vx = 0;
                    a.vy = 0;
                    b.vx = 0;
                    b.vy = 0;
                    clamp(a);
                    clamp(b);
                }
            }
        }

        out.snapshots.push_back({frame, fold_d(world)});
    }
    out.final_digest = out.snapshots.empty() ? fold_d(world) : out.snapshots.back().digest;
    return out;
}

}  // namespace vx
