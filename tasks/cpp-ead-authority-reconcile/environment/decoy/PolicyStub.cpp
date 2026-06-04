#include <string>

namespace arc_decoy {

bool prefix_matches(const std::string& value, const std::string& prefix) {
  return value.rfind(prefix, 0) == 0;
}

}  // namespace arc_decoy
