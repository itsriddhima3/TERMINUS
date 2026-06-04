#include "arc/stages.hpp"

#include <nlohmann/json.hpp>

namespace arc {

nlohmann::json load_parsed_records(const std::string& batch_id);
void write_parsed_records(const nlohmann::json& records);

int exec_parse_stage(const std::string& batch_id) {
  auto records = load_parsed_records(batch_id);
  write_parsed_records(records);
  return 0;
}

}  // namespace arc
