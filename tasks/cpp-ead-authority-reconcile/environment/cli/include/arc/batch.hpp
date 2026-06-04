#pragma once

#include <nlohmann/json.hpp>
#include <string>

namespace arc {

nlohmann::json load_batch(const std::string& batch_id);

}  // namespace arc
