#pragma once

#include <filesystem>
#include <vector>

#include "vx/types.hpp"

namespace vx {

void write_report(const std::vector<Row>& rows, const std::filesystem::path& out_path);

}  // namespace vx
