#include <iostream>

#include "vx/audit.hpp"
#include "vx/files.hpp"
#include "vx/report.hpp"

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: velox_probe <capture-dir> <report-json>\n";
        return 2;
    }

    try {
        std::vector<vx::Row> rows;
        for (const auto& item : vx::load_cases(argv[1])) {
            rows.push_back(vx::scan_d(item));
        }
        vx::write_report(rows, argv[2]);
    } catch (const std::exception& ex) {
        std::cerr << ex.what() << "\n";
        return 1;
    }
    return 0;
}
