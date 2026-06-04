#include "arc/net_ops.hpp"

#include "arc/http.hpp"

#include <cctype>
#include <sstream>
#include <string>

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

std::string strip_paren_place(const std::string& name) {
  auto p = name.find(" (");
  if (p != std::string::npos) {
    return name.substr(0, p);
  }
  return name;
}

}  // namespace

std::string query_place(const std::string& name, bool approx) {
  std::string lookup = strip_paren_place(name);
  int tier = approx ? 2 : 1;
  std::ostringstream url;
  url << "http://127.0.0.1:3000/api/v1/places/resolve?name=" << url_encode(lookup)
      << "&tier=" << tier;
  std::string body = http_get(url.str());
  if (body.empty()) return "";
  auto j = nlohmann::json::parse(body, nullptr, false);
  if (j.is_discarded() || !j.contains("place_id")) return "";
  return j["place_id"].get<std::string>();
}

}  // namespace arc
