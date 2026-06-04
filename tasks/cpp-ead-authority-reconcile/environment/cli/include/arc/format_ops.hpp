#pragma once

#include <string>

#include <nlohmann/json.hpp>

namespace arc {

std::string format_unitdate(const std::string& raw);
std::string emit_csv_row(const nlohmann::json& row);

}  // namespace arc
