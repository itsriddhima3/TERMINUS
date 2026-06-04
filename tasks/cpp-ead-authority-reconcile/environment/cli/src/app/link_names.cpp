#include "arc/link_ops.hpp"
#include "arc/net_ops.hpp"
#include "arc/paths.hpp"
#include "arc/scan_ops.hpp"

#include <libxml/parser.h>
#include <sstream>
#include <vector>

#include <nlohmann/json.hpp>

namespace arc {

namespace {

std::string join_ids(const std::vector<std::string>& ids) {
  std::ostringstream o;
  for (size_t i = 0; i < ids.size(); ++i) {
    if (i) o << ';';
    o << ids[i];
  }
  return o.str();
}

}  // namespace

nlohmann::json link_creator_fields(const nlohmann::json& rec) {
  std::string fname = rec["source_file"];
  std::filesystem::path path = ead_root() / fname;
  xmlDocPtr xdoc = xmlReadFile(path.c_str(), nullptr, 0);
  std::vector<std::pair<std::string, std::string>> names;
  if (xdoc) {
    walk_controlaccess_names(xmlDocGetRootElement(xdoc), names);
    xmlFreeDoc(xdoc);
  }
  std::string creator_auth = pick_creator_auth(names);
  std::vector<std::string> subj_ids;
  for (const auto& subj : rec["subjects"]) {
    std::string head = strip_subject_head(subj.get<std::string>());
    std::string id = resolve_subject(head);
    if (!id.empty()) subj_ids.push_back(id);
  }
  return {
      {"creator_primary", creator_auth},
      {"subject_headings", join_ids(subj_ids)},
  };
}

}  // namespace arc
