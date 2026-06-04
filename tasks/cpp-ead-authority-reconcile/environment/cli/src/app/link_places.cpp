#include "arc/net_ops.hpp"
#include "arc/policy_ops.hpp"

#include <nlohmann/json.hpp>
#include <sstream>
#include <vector>

namespace arc {

namespace {

std::string join_ids(const std::vector<std::string>& ids) {
  std::ostringstream o;
  for (size_t i = 0; i < ids.size(); ++i) {
    if (i) o << ';';
    o << ids[i];
  }
  return o.str();
}

}  // namespace

nlohmann::json link_place_fields(const nlohmann::json& rec) {
  std::vector<std::string> place_ids;
  for (const auto& pl : rec["places"]) {
    std::string id = query_place(pl["name"], pl["approx"]);
    if (!id.empty()) place_ids.push_back(id);
  }
  std::string collection_id = rec["collection_id"];
  std::string accession = apply_accession_precedence(collection_id);
  bool acc_ok = accession_valid(collection_id, accession);
  return {
      {"place_names", join_ids(place_ids)},
      {"accession_candidate", accession},
      {"accession_valid", acc_ok},
  };
}

}  // namespace arc
