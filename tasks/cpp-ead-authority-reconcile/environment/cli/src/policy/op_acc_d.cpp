#include "arc/policy_ops.hpp"

#include "arc/http.hpp"

#include <sstream>

#include <nlohmann/json.hpp>

namespace arc {

std::string format_accession_candidate(const std::string& collection_id) {
  if (collection_id.rfind("MS-", 0) == 0) {
    return std::string("MSS-") + collection_id.substr(3);
  }
  return collection_id;
}

bool accession_valid(const std::string& collection_id, const std::string& candidate) {
  std::ostringstream url;
  url << "http://127.0.0.1:3000/api/v1/accession/validate?collection_id="
      << collection_id << "&candidate=" << candidate;
  std::string body = http_get(url.str());
  if (body.empty()) return false;
  auto j = nlohmann::json::parse(body, nullptr, false);
  if (j.is_discarded() || !j.contains("valid")) return false;
  return j["valid"].get<bool>();
}

}  // namespace arc
