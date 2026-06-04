#pragma once

#include <string>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

namespace arc {

struct EadFields {
  std::string collection_id;
  std::string title;
  std::string unitdate_raw;
  std::string date_span;
  std::vector<std::pair<std::string, std::string>> creators;
  std::vector<std::string> subjects;
  std::vector<std::pair<std::string, bool>> places;
};

}  // namespace arc
