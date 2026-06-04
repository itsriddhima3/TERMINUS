#pragma once

#include <string>

namespace arc {

int exec_parse_stage(const std::string& batch_id);
int exec_link_stage(const std::string& batch_id);
int exec_report_stage(const std::string& batch_id);

}  // namespace arc
