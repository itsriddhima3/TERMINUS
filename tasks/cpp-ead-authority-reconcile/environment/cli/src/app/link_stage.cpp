#include "arc/stages.hpp"
#include "arc/paths.hpp"

#include <fstream>
#include <iostream>

#include <nlohmann/json.hpp>

namespace arc {

nlohmann::json link_creator_fields(const nlohmann::json& rec);
nlohmann::json link_place_fields(const nlohmann::json& rec);

int exec_link_stage(const std::string& batch_id) {
  std::filesystem::path src = var_dir() / "records.jsonl";
  std::ifstream in(src);
  nlohmann::json linked = nlohmann::json::array();
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    auto rec = nlohmann::json::parse(line);
    auto creator = link_creator_fields(rec);
    auto places = link_place_fields(rec);
    linked.push_back({
        {"collection_id", rec["collection_id"]},
        {"title", rec["title"]},
        {"date_span", rec["date_span"]},
        {"creator_primary", creator["creator_primary"]},
        {"subject_headings", creator["subject_headings"]},
        {"place_names", places["place_names"]},
        {"geo_heading_count", rec["places"].size()},
        {"subject_heading_count", rec["subjects"].size()},
        {"accession_candidate", places["accession_candidate"]},
        {"accession_valid", places["accession_valid"]},
    });
  }
  nlohmann::json out{{"batch_id", batch_id}, {"records", linked}};
  std::filesystem::path dest = output_dir() / "linked.json";
  std::ofstream ofs(dest);
  ofs << out.dump(2);
  std::cout << "linked " << linked.size() << " records -> " << dest << "\n";
  return 0;
}

}  // namespace arc
