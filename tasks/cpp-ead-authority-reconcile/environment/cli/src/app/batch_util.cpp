#include "arc/batch.hpp"
#include "arc/paths.hpp"

#include <nlohmann/json.hpp>
#include <stdexcept>

namespace arc {

nlohmann::json load_batch(const std::string& batch_id) {
  auto reg = nlohmann::json::parse(read_text_file(config_dir() / "batch_registry.json"));
  for (const auto& b : reg["batches"]) {
    if (b["batch_id"] == batch_id) {
      return b;
    }
  }
  throw std::runtime_error("unknown batch: " + batch_id);
}

}  // namespace arc
