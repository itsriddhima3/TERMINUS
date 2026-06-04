#pragma once

#include <nlohmann/json.hpp>

namespace arc {

nlohmann::json filter_report_queue(const nlohmann::json& rows);

}  // namespace arc
