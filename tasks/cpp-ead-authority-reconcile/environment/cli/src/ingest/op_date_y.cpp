#include "arc/format_ops.hpp"

#include <sstream>

namespace arc {

std::string format_unitdate(const std::string& raw) {
  auto slash = raw.find('/');
  if (slash == std::string::npos) {
    return raw;
  }
  std::string a = raw.substr(0, slash);
  std::string b = raw.substr(slash + 1);
  if (a.size() >= 4) a = a.substr(a.size() - 2);
  if (b.size() >= 4) b = b.substr(b.size() - 2);
  return a + "-" + b;
}

}  // namespace arc
