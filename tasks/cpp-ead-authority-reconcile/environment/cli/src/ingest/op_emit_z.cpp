#include "arc/format_ops.hpp"

#include <sstream>

namespace arc {

static std::string esc(const std::string& v) {
  if (v.find(',') != std::string::npos || v.find('"') != std::string::npos) {
    std::ostringstream o;
    o << '"';
    for (char c : v) {
      if (c == '"') o << "\"\"";
      else o << c;
    }
    o << '"';
    return o.str();
  }
  return v;
}

std::string emit_csv_row(const nlohmann::json& row) {
  std::ostringstream o;
  o << esc(row.value("title", "")) << ','
    << esc(row.value("collection_id", "")) << ','
    << esc(row.value("date_span", "")) << ','
    << esc(row.value("creator_primary", "")) << ','
    << esc(row.value("subject_headings", "")) << ','
    << esc(row.value("place_names", ""));
  return o.str();
}

}  // namespace arc
