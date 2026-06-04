#pragma once

#include <string>
#include <vector>

namespace vx {

struct Unit {
    std::string id;
    std::string team;
    long long x = 0;
    long long y = 0;
    long long vx = 0;
    long long vy = 0;
    long long hp = 0;
    long long radius = 0;
};

struct Event {
    int frame = 0;
    int seq = 0;
    std::string unit;
    std::string op;
    std::string a;
    std::string b;
    std::string c;
};

struct Capture {
    std::string id;
    int frames = 0;
    int reload_frame = -1;  // script boundary frame from capture reload line
    std::string reload_tag;
    std::vector<Unit> units;
    std::vector<Event> original;
    std::vector<Event> playback;
};

struct Snapshot {
    int frame = 0;
    std::string digest;
};

struct Run {
    std::string final_digest;
    std::vector<Snapshot> snapshots;
};

struct Row {
    std::string id;
    std::string status;
    int first_bad_frame = -1;
    std::string reason;
    std::string source;
    std::string original_digest;
    std::string replay_digest;
    int frames = 0;
};

}  // namespace vx
