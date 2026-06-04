#include "arc/net_ops.hpp"

#include "arc/http.hpp"

#include <cctype>
#include <sstream>

#include <nlohmann/json.hpp>

namespace arc {

namespace {

std::string url_encode(const std::string& s) {
  std::ostringstream o;
  for (unsigned char c : s) {
    if (std::isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
      o << c;
    } else {
      o << '%' << std::hex << std::uppercase;
      o.width(2);
      o.fill('0');
      o << static_cast<int>(c);
      o << std::dec;
    }
  }
  return o.str();
}

std::string parse_id_field(const std::string& body, const char* key) {
  if (body.empty()) return "";
  auto j = nlohmann::json::parse(body, nullptr, false);
  if (j.is_discarded() || !j.contains(key)) return "";
  return j[key].get<std::string>();
}

}  // namespace

std::string resolve_creator(const std::string& name) {
  std::ostringstream url;
  url << "http://127.0.0.1:3000/api/v1/creators/resolve?name=" << url_encode(name);
  return parse_id_field(http_get(url.str()), "auth_id");
}

std::string resolve_subject(const std::string& head) {
  std::ostringstream url;
  url << "http://127.0.0.1:3000/api/v1/subjects/resolve?head=" << url_encode(head)
      << "&tier=1";
  return parse_id_field(http_get(url.str()), "subj_id");
}

}  // namespace arc
