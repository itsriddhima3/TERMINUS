#include "arc/scan_ops.hpp"

#include <libxml/tree.h>
#include <cstring>

namespace arc {

namespace {

xmlNodePtr find_child(xmlNodePtr parent, const char* name) {
  for (xmlNodePtr c = parent ? parent->children : nullptr; c; c = c->next) {
    if (c->type == XML_ELEMENT_NODE && xmlStrcmp(c->name, BAD_CAST name) == 0) {
      return c;
    }
  }
  return nullptr;
}

xmlNodePtr find_desc(xmlNodePtr root, const char* name) {
  if (!root) return nullptr;
  if (root->type == XML_ELEMENT_NODE && xmlStrcmp(root->name, BAD_CAST name) == 0) {
    return root;
  }
  for (xmlNodePtr c = root->children; c; c = c->next) {
    xmlNodePtr hit = find_desc(c, name);
    if (hit) return hit;
  }
  return nullptr;
}

std::string text_of(xmlNodePtr n) {
  if (!n) return "";
  xmlChar* t = xmlNodeGetContent(n);
  std::string s = t ? reinterpret_cast<const char*>(t) : "";
  xmlFree(t);
  return s;
}

void trim(std::string& s) {
  while (!s.empty() && (s.front() == ' ' || s.front() == '\n')) s.erase(s.begin());
  while (!s.empty() && (s.back() == ' ' || s.back() == '\n')) s.pop_back();
}

}  // namespace

void scan_controlaccess(xmlNodePtr root, EadFields& out) {
  xmlNodePtr arch = find_desc(root, "archdesc");
  if (!arch) return;
  xmlNodePtr did = find_child(arch, "did");
  if (did) {
    out.collection_id = text_of(find_child(did, "unitid"));
    out.title = text_of(find_child(did, "unittitle"));
    xmlNodePtr ud = find_child(did, "unitdate");
    if (ud) {
      const char* norm = reinterpret_cast<const char*>(xmlGetProp(ud, BAD_CAST "normal"));
      out.unitdate_raw = norm ? norm : text_of(ud);
    }
  }
  xmlNodePtr ca = find_child(arch, "controlaccess");
  if (!ca) return;
  for (xmlNodePtr c = ca->children; c; c = c->next) {
    if (c->type != XML_ELEMENT_NODE) continue;
    if (xmlStrcmp(c->name, BAD_CAST "corpname") == 0) {
      std::string nm = text_of(c);
      trim(nm);
      out.creators.emplace_back("corp", nm);
    } else if (xmlStrcmp(c->name, BAD_CAST "persname") == 0) {
      continue;
    } else if (xmlStrcmp(c->name, BAD_CAST "subject") == 0) {
      std::string subj = text_of(c);
      trim(subj);
      out.subjects.push_back(subj);
    } else if (xmlStrcmp(c->name, BAD_CAST "geogname") == 0) {
      bool approx = xmlGetProp(c, BAD_CAST "approx") != nullptr;
      std::string place = text_of(c);
      trim(place);
      out.places.emplace_back(place, approx);
    }
  }
}

void walk_controlaccess_names(xmlNodePtr root, std::vector<std::pair<std::string, std::string>>& out) {
  xmlNodePtr arch = find_desc(root, "archdesc");
  if (!arch) return;
  xmlNodePtr ca = find_child(arch, "controlaccess");
  if (!ca) return;
  for (xmlNodePtr c = ca->children; c; c = c->next) {
    if (c->type != XML_ELEMENT_NODE) continue;
    if (xmlStrcmp(c->name, BAD_CAST "corpname") == 0) {
      std::string nm = text_of(c);
      trim(nm);
      out.emplace_back("corp", nm);
    } else if (xmlStrcmp(c->name, BAD_CAST "persname") == 0) {
      std::string nm = text_of(c);
      trim(nm);
      out.emplace_back("pers", nm);
    }
  }
}

}  // namespace arc
