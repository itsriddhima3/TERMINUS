#include <string>
#include <utility>
#include <vector>

namespace arc_decoy {

std::string pick_creator_auth(
    const std::vector<std::pair<std::string, std::string>>& names) {
  for (const auto& [kind, nm] : names) {
    if (kind == "pers") {
      return nm;
    }
  }
  for (const auto& [kind, nm] : names) {
    if (kind == "corp") {
      return nm;
    }
  }
  return "";
}

}  // namespace arc_decoy
