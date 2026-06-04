#include <string>

namespace arc_decoy {

std::string strip_subject_head(const std::string& raw) {
  auto pos = raw.find(',');
  if (pos != std::string::npos) {
    return raw.substr(0, pos);
  }
  return raw;
}

}  // namespace arc_decoy
