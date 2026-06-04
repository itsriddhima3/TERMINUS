#include "page.h"

#include <regex>

std::vector<std::string> parse_html_pages(const std::string &html) {
  std::vector<std::string> out;
  std::regex re(R"(href="[^"]*page=(\d+))");
  auto begin = std::sregex_iterator(html.begin(), html.end(), re);
  auto end = std::sregex_iterator();
  for (auto it = begin; it != end; ++it) {
    out.push_back((*it)[1].str());
  }
  return out;
}
