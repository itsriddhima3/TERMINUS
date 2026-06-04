#include "arc/report_ops.hpp"

namespace arc {

nlohmann::json filter_report_queue(const nlohmann::json& rows) {
  nlohmann::json kept = nlohmann::json::array();
  for (const auto& row : rows) {
    bool unresolved = row.value("subject_headings", "").empty() ||
                      row.value("creator_primary", "").empty() ||
                      row.value("place_names", "").empty() ||
                      !row.value("accession_valid", false);
    if (unresolved) {
      continue;
    }
    kept.push_back(row);
  }
  return kept;
}

}  // namespace arc
