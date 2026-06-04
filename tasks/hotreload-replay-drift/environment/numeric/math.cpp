#include "vx/math.hpp"

#include <iomanip>
#include <sstream>

namespace vx {

long long fold_m(const std::string& x) {
    std::size_t dot = x.find('.');
    std::string whole = dot == std::string::npos ? x : x.substr(0, dot);
    std::string frac = dot == std::string::npos ? "" : x.substr(dot + 1);
    if (whole.empty()) {
        whole = "0";
    }
    while (frac.size() < 3) {
        frac.push_back('0');
    }
    long long value = std::stoll(whole) * 1000;
    value += std::stoll(frac.substr(0, 3));
    if (frac.size() > 3 && frac[3] >= '5') {
        value += 1;
    }
    return value;
}

std::string unit_text(long long x) {
    std::ostringstream out;
    if (x < 0) {
        out << '-';
        x = -x;
    }
    out << (x / 1000) << '.' << std::setw(3) << std::setfill('0') << (x % 1000);
    return out.str();
}

}  // namespace vx
