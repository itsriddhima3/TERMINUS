#include "vx/report.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace vx {
namespace {

std::string esc(const std::string& s) {
    std::string out;
    for (char c : s) {
        if (c == '"' || c == '\\') {
            out.push_back('\\');
        }
        out.push_back(c);
    }
    return out;
}

}  // namespace

void write_report(const std::vector<Row>& rows, const std::filesystem::path& out_path) {
    auto ordered = rows;
    std::sort(ordered.begin(), ordered.end(), [](const Row& a, const Row& b) {
        return a.id < b.id;
    });

    int stable = 0;
    int drifted = 0;
    for (const auto& row : ordered) {
        if (row.status == "stable") {
            ++stable;
        } else {
            ++drifted;
        }
    }

    std::filesystem::create_directories(out_path.parent_path());
    std::ofstream out(out_path);
    if (!out) {
        throw std::runtime_error("cannot write report: " + out_path.string());
    }

    out << "{\"summary\":{\"checked\":" << ordered.size()
        << ",\"stable\":" << stable
        << ",\"drifted\":" << drifted
        << "},\"sessions\":[";
    for (std::size_t i = 0; i < ordered.size(); ++i) {
        const auto& row = ordered[i];
        if (i) {
            out << ',';
        }
        out << "{\"id\":\"" << esc(row.id) << "\""
            << ",\"status\":\"" << esc(row.status) << "\""
            << ",\"first_bad_frame\":";
        if (row.first_bad_frame < 0) {
            out << "null";
        } else {
            out << row.first_bad_frame;
        }
        out << ",\"reason\":\"" << esc(row.reason) << "\""
            << ",\"source\":\"" << esc(row.source) << "\""
            << ",\"original_digest\":\"" << esc(row.original_digest) << "\""
            << ",\"replay_digest\":\"" << esc(row.replay_digest) << "\""
            << ",\"frames\":" << row.frames << "}";
    }
    out << "]}\n";
}

}  // namespace vx
