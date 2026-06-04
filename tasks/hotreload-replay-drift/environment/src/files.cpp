#include "vx/files.hpp"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <stdexcept>

#include "vx/config.hpp"
#include "vx/math.hpp"

namespace vx {
namespace {

std::string trim(const std::string& s) {
    const auto b = s.find_first_not_of(" \t\r\n");
    if (b == std::string::npos) {
        return "";
    }
    const auto e = s.find_last_not_of(" \t\r\n");
    return s.substr(b, e - b + 1);
}

Capture read_one(const std::filesystem::path& path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("cannot open capture: " + path.string());
    }

    Capture c;
    std::string section;
    std::string line;
    int line_no = 0;
    while (std::getline(in, line)) {
        ++line_no;
        line = trim(line);
        if (line.empty() || line[0] == '#') {
            continue;
        }
        std::istringstream ss(line);
        std::string word;
        ss >> word;
        if (word == "session") {
            ss >> c.id;
        } else if (word == "frames") {
            ss >> c.frames;
            if (c.frames < 1 || c.frames > max_reasonable_frames()) {
                throw std::runtime_error("bad frame count in " + path.string());
            }
        } else if (word == "reload") {
            ss >> c.reload_frame >> c.reload_tag;
        } else if (word == "body") {
            Unit u;
            std::string x, y, vx, vy, hp, radius;
            ss >> u.id >> u.team >> x >> y >> vx >> vy >> hp >> radius;
            u.x = fold_m(x);
            u.y = fold_m(y);
            u.vx = fold_m(vx);
            u.vy = fold_m(vy);
            u.hp = fold_m(hp);
            u.radius = fold_m(radius);
            c.units.push_back(u);
        } else if (word == "original" || word == "playback") {
            section = word;
        } else if (word == "end") {
            section.clear();
        } else if (word == "event") {
            if (section.empty()) {
                throw std::runtime_error("event outside section at line " + std::to_string(line_no));
            }
            Event e;
            ss >> e.frame >> e.seq >> e.unit >> e.op >> e.a >> e.b >> e.c;
            if (section == "original") {
                c.original.push_back(e);
            } else {
                c.playback.push_back(e);
            }
        }
    }
    if (c.id.empty()) {
        c.id = path.stem().string();
    }
    return c;
}

}  // namespace

std::vector<Capture> load_cases(const std::filesystem::path& root) {
    std::vector<std::filesystem::path> paths;
    for (const auto& entry : std::filesystem::directory_iterator(root)) {
        if (entry.is_regular_file()) {
            paths.push_back(entry.path());
        }
    }
    std::sort(paths.begin(), paths.end());

    std::vector<Capture> out;
    out.reserve(paths.size());
    for (const auto& path : paths) {
        out.push_back(read_one(path));
    }
    return out;
}

}  // namespace vx
