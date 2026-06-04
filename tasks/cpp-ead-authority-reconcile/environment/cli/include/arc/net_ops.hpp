#pragma once

#include <string>

namespace arc {

std::string query_place(const std::string& name, bool approx);
std::string resolve_creator(const std::string& name);
std::string resolve_subject(const std::string& head);

}  // namespace arc
