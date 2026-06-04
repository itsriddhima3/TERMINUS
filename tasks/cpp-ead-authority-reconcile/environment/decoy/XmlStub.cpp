#include <libxml/parser.h>
#include <string>

namespace arc_decoy {

std::string node_local_name(xmlNodePtr node) {
  if (!node || node->type != XML_ELEMENT_NODE) return "";
  return reinterpret_cast<const char*>(node->name);
}

}  // namespace arc_decoy
