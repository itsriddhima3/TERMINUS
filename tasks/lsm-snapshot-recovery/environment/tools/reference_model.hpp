#pragma once

#include "tile/tile.hpp"

#include <nlohmann/json.hpp>

#include <filesystem>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace ts {

class ReferenceFromWal {
 public:
  void replay(const std::filesystem::path& wal_path);
  std::string get(const std::string& key) const;
  std::string scan(const std::string& start, const std::string& end) const;
  nlohmann::json structure_snapshot() const;
  int layout_generation() const { return layout_gen_; }

 private:
  void hard_reset();
  void apply_line(const nlohmann::json& rec);
  void materialize_buffer_to_tile();
  void persist_tile_file(int tile_id, const std::map<std::string, std::string>& rows) const;

  std::filesystem::path data_dir_;
  std::vector<TileChunk> tiles_;
  std::map<std::string, std::string> buffer_;
  std::vector<std::map<std::string, std::string>> pin_vals_;
  std::vector<std::set<std::string>> pin_tombs_;
  int layout_gen_{0};
  int next_tile_{1};
  bool has_pin_{false};
};

}  // namespace ts
