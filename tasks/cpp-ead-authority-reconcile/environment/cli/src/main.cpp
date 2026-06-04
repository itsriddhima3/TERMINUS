#include "arc/paths.hpp"

#include <libxml/parser.h>
#include <iostream>
#include <string>

namespace arc {
int run_parse(const std::string& batch_id);
int run_link(const std::string& batch_id);
int run_report(const std::string& batch_id);
}  // namespace arc

int main(int argc, char** argv) {
  xmlInitParser();
  int rc = 2;
  try {
    if (argc < 3) {
      std::cerr << "usage: arcctl <parse|link|report> <batch-id>\n";
      rc = 2;
    } else {
      std::string verb = argv[1];
      std::string batch = argv[2];
      if (verb == "parse") {
        rc = arc::run_parse(batch);
      } else if (verb == "link") {
        rc = arc::run_link(batch);
      } else if (verb == "report") {
        rc = arc::run_report(batch);
      } else {
        std::cerr << "unknown verb: " << verb << "\n";
        rc = 2;
      }
    }
  } catch (const std::exception& ex) {
    std::cerr << "error: " << ex.what() << "\n";
    rc = 1;
  }
  xmlCleanupParser();
  return rc;
}
