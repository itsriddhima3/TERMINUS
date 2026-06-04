#include "arc/format_ops.hpp"
#include "arc/paths.hpp"

#include <fstream>
#include <iostream>

#include <nlohmann/json.hpp>

namespace arc {

void write_parsed_records(const nlohmann::json& records) {
  std::filesystem::path jsonl_path = var_dir() / "records.jsonl";
  std::ofstream jsonl(jsonl_path);
  for (const auto& rec : records) {
    jsonl << rec.dump() << "\n";
  }
  std::filesystem::path csv_path = var_dir() / "records.csv";
  std::ofstream csv(csv_path);
  csv << "collection_id,title,date_span,creator_primary,subject_headings,place_names\n";
  for (const auto& rec : records) {
    csv << emit_csv_row(rec) << "\n";
  }
  std::cout << "parsed " << records.size() << " records -> " << jsonl_path
            << " and " << csv_path << "\n";
}

}  // namespace arc
