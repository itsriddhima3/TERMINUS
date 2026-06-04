#include "arc/batch.hpp"
#include "arc/fields.hpp"
#include "arc/fields.hpp"
#include "arc/format_ops.hpp"
#include "arc/scan_ops.hpp"
#include "arc/paths.hpp"

#include <libxml/parser.h>
#include <sstream>
#include <stdexcept>

#include <nlohmann/json.hpp>

namespace arc {

namespace {

nlohmann::json fields_to_json(const EadFields& f, const std::string& source_file) {
  nlohmann::json creators = nlohmann::json::array();
  std::string creator_primary;
  for (const auto& [kind, name] : f.creators) {
    creators.push_back({{"type", kind}, {"name", name}});
    if (creator_primary.empty()) creator_primary = name;
  }
  nlohmann::json subjects = nlohmann::json::array();
  std::ostringstream subj_join;
  for (size_t i = 0; i < f.subjects.size(); ++i) {
    if (i) subj_join << ';';
    subj_join << f.subjects[i];
    subjects.push_back(f.subjects[i]);
  }
  nlohmann::json places = nlohmann::json::array();
  std::ostringstream place_join;
  for (size_t i = 0; i < f.places.size(); ++i) {
    if (i) place_join << ';';
    place_join << f.places[i].first;
    places.push_back({{"name", f.places[i].first}, {"approx", f.places[i].second}});
  }
  return {
      {"source_file", source_file},
      {"collection_id", f.collection_id},
      {"title", f.title},
      {"unitdate_raw", f.unitdate_raw},
      {"date_span", f.date_span},
      {"creator_primary", creator_primary},
      {"subject_headings", subj_join.str()},
      {"place_names", place_join.str()},
      {"creators", creators},
      {"subjects", subjects},
      {"places", places},
  };
}

}  // namespace

nlohmann::json load_parsed_records(const std::string& batch_id) {
  auto batch = load_batch(batch_id);
  nlohmann::json records = nlohmann::json::array();
  for (const auto& file : batch["files"]) {
    std::string fname = file.get<std::string>();
    std::filesystem::path path = ead_root() / fname;
    xmlDocPtr doc = xmlReadFile(path.c_str(), nullptr, 0);
    if (!doc) {
      throw std::runtime_error("failed to parse ead: " + fname);
    }
    EadFields fields;
    scan_controlaccess(xmlDocGetRootElement(doc), fields);
    fields.date_span = format_unitdate(fields.unitdate_raw);
    records.push_back(fields_to_json(fields, fname));
    xmlFreeDoc(doc);
  }
  return records;
}

}  // namespace arc
