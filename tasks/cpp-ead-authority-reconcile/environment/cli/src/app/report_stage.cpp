#include "arc/stages.hpp"
#include "arc/paths.hpp"
#include "arc/report_ops.hpp"

#include <fstream>
#include <iostream>

#include <nlohmann/json.hpp>

namespace arc {

int exec_report_stage(const std::string& batch_id) {
  std::filesystem::path src = output_dir() / "linked.json";
  auto doc = nlohmann::json::parse(read_text_file(src));
  auto rows = doc["records"];
  nlohmann::json unresolved = nlohmann::json::array();
  int acc_pass = 0;
  int acc_fail = 0;
  int fully_linked = 0;
  for (const auto& row : rows) {
    bool needs_place = row.value("geo_heading_count", 0) > 0;
    bool needs_subject = row.value("subject_heading_count", 0) > 0;
    bool bad = (needs_subject && row.value("subject_headings", "").empty()) ||
               row.value("creator_primary", "").empty() ||
               (needs_place && row.value("place_names", "").empty()) ||
               !row.value("accession_valid", false);
    if (bad) {
      unresolved.push_back(row);
    } else {
      fully_linked += 1;
    }
    if (row.value("accession_valid", false)) {
      acc_pass += 1;
    } else {
      acc_fail += 1;
    }
  }
  auto kept = filter_report_queue(rows);
  nlohmann::json compliance{
      {"batch_id", batch_id},
      {"summary",
       {{"total", rows.size()},
        {"accession_pass", acc_pass},
        {"accession_fail", acc_fail},
        {"fully_linked", fully_linked},
        {"unresolved_count", unresolved.size()}}},
      {"records", kept},
  };
  std::filesystem::path comp_path = output_dir() / "compliance.json";
  std::ofstream comp(comp_path);
  comp << compliance.dump(2);
  std::filesystem::path unres_path = output_dir() / "unresolved.jsonl";
  std::ofstream unres(unres_path);
  for (const auto& row : unresolved) {
    unres << row.dump() << "\n";
  }
  std::cout << "report compliance -> " << comp_path << " unresolved -> " << unres_path
            << "\n";
  return 0;
}

}  // namespace arc
