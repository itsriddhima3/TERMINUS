#include "arc/stages.hpp"

namespace arc {

int exec_parse_stage(const std::string& batch_id);

}  // namespace arc

namespace arc {

int run_parse(const std::string& batch_id) { return exec_parse_stage(batch_id); }

}  // namespace arc
