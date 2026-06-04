#include "arc/policy_ops.hpp"

#include "arc/paths.hpp"

#include <fstream>
#include <string>

namespace arc {

namespace {

bool bench_ms_dot_override() {
  std::ifstream in(arc::config_dir() / "bench_policy.toml");
  std::string line;
  while (std::getline(in, line)) {
    if (line.find("ms_use_dot") != std::string::npos && line.find("true") != std::string::npos) {
      return true;
    }
  }
  return false;
}

}  // namespace

std::string apply_accession_precedence(const std::string& collection_id) {
  if (collection_id.rfind("MS-", 0) == 0) {
    if (bench_ms_dot_override()) {
      return format_accession_candidate(collection_id);
    }
    return collection_id;
  }
  return format_accession_candidate(collection_id);
}

}  // namespace arc
