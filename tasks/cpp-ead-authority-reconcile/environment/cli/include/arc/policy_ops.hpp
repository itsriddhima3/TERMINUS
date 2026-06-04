#pragma once

#include <string>

namespace arc {

std::string format_accession_candidate(const std::string& collection_id);
std::string apply_accession_precedence(const std::string& collection_id);
bool accession_valid(const std::string& collection_id, const std::string& candidate);

}  // namespace arc
