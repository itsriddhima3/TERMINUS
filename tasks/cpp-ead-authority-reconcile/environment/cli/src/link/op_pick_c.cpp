#include "arc/link_ops.hpp"
#include "arc/net_ops.hpp"

namespace arc {

std::string pick_creator_auth(const std::vector<std::pair<std::string, std::string>>& names) {
  for (const auto& [kind, nm] : names) {
    if (kind == "pers") {
      std::string auth = resolve_creator(nm);
      if (!auth.empty()) return auth;
    }
  }
  for (const auto& [kind, nm] : names) {
    if (kind == "corp") {
      std::string auth = resolve_creator(nm);
      if (!auth.empty()) return auth;
    }
  }
  return "";
}

}  // namespace arc
