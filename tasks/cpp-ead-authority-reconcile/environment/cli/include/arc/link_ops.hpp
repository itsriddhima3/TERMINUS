#pragma once

#include <string>
#include <utility>
#include <vector>

namespace arc {

std::string strip_subject_head(const std::string& raw);
std::string pick_creator_auth(const std::vector<std::pair<std::string, std::string>>& names);

}  // namespace arc
