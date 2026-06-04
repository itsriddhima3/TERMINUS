#pragma once

#include <filesystem>
#include <vector>

#include "vx/types.hpp"

namespace vx {

std::vector<Capture> load_cases(const std::filesystem::path& root);

}  // namespace vx
