#pragma once

#include <libxml/tree.h>
#include <string>
#include <utility>
#include <vector>

#include "arc/fields.hpp"

namespace arc {

void scan_controlaccess(xmlNodePtr root, EadFields& out);
void walk_controlaccess_names(xmlNodePtr root, std::vector<std::pair<std::string, std::string>>& out);

}  // namespace arc
