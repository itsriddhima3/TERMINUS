#include "reference_model.hpp"

#include "cursor_pin/pin.hpp"

#include <fstream>

namespace ts {

namespace {
constexpr const char* kTomb = "__T__";

TileChunk fold_correct(const TileChunk& older, const TileChunk& newer) {
  TileChunk out;
  out.id = newer.id;
  for (const auto& [k, v] : newer.rows) {
    out.rows[k] = v;
  }
  for (const auto& [k, v] : older.rows) {
    if (out.rows.find(k) == out.rows.end()) {
      out.rows[k] = v;
    }
  }
  return out;
}

ViewSnap materialize_from(const std::vector<TileChunk>& tiles,
                          const std::map<std::string, std::string>& buffer) {
  ViewSnap acc;
  for (const auto& ch : tiles) {
    acc = merge_overlay(acc, ch.rows);
  }
  acc = merge_overlay(acc, buffer);
  return acc;
}
}  // namespace

void ReferenceFromWal::hard_reset() {
  tiles_.clear();
  buffer_.clear();
  pin_vals_.clear();
  pin_tombs_.clear();
  has_pin_ = false;
  layout_gen_ = 0;
  next_tile_ = 1;
}

void ReferenceFromWal::materialize_buffer_to_tile() {
  if (buffer_.empty()) {
    return;
  }
  TileChunk ch;
  ch.id = next_tile_++;
  ch.rows = buffer_;
  tiles_.push_back(std::move(ch));
  buffer_.clear();
  persist_tile_file(tiles_.back().id, tiles_.back().rows);
}

void ReferenceFromWal::persist_tile_file(int tile_id,
                                         const std::map<std::string, std::string>& rows) const {
  std::filesystem::path p = data_dir_ / ("tile_" + std::to_string(tile_id) + ".dat");
  std::ofstream out(p);
  for (const auto& [k, v] : rows) {
    out << k << '\t' << v << '\n';
  }
}

void ReferenceFromWal::apply_line(const nlohmann::json& rec) {
  const std::string op = rec.at("op").get<std::string>();
  if (op == "put") {
    buffer_[rec.at("key").get<std::string>()] = rec.at("value").get<std::string>();
  } else if (op == "obliterate") {
    buffer_[rec.at("key").get<std::string>()] = kTomb;
  } else if (op == "flush") {
    materialize_buffer_to_tile();
  } else if (op == "merge") {
    if (tiles_.size() >= 2) {
      TileChunk older = tiles_[tiles_.size() - 2];
      TileChunk newer = tiles_.back();
      TileChunk folded = fold_correct(older, newer);
      tiles_.pop_back();
      tiles_.pop_back();
      tiles_.push_back(folded);
      persist_tile_file(folded.id, folded.rows);
    }
  } else if (op == "open_pin") {
    ViewSnap snap = materialize_from(tiles_, buffer_);
    pin_vals_.push_back(snap.vals);
    pin_tombs_.push_back(snap.tombs);
    has_pin_ = true;
  } else if (op == "close_pin") {
    if (!pin_vals_.empty()) {
      pin_vals_.pop_back();
      pin_tombs_.pop_back();
    }
    has_pin_ = !pin_vals_.empty();
  } else if (op == "layout_bump") {
    layout_gen_ += rec.at("delta").get<int>();
  }
}

void ReferenceFromWal::replay(const std::filesystem::path& wal_path) {
  data_dir_ = wal_path.parent_path();
  hard_reset();
  std::ifstream in(wal_path);
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty()) {
      continue;
    }
    try {
      nlohmann::json rec = nlohmann::json::parse(line);
      apply_line(rec);
    } catch (const nlohmann::json::exception&) {
      break;
    }
  }
}

std::string ReferenceFromWal::get(const std::string& key) const {
  if (has_pin_ && !pin_vals_.empty()) {
    ViewSnap frozen;
    frozen.vals = pin_vals_.back();
    frozen.tombs = pin_tombs_.back();
    return encode_get(frozen, key);
  }
  return encode_get(materialize_from(tiles_, buffer_), key);
}

std::string ReferenceFromWal::scan(const std::string& start, const std::string& end) const {
  if (has_pin_ && !pin_vals_.empty()) {
    ViewSnap frozen;
    frozen.vals = pin_vals_.back();
    frozen.tombs = pin_tombs_.back();
    return encode_scan(frozen, start, end);
  }
  return encode_scan(materialize_from(tiles_, buffer_), start, end);
}

nlohmann::json ReferenceFromWal::structure_snapshot() const {
  nlohmann::json tiles = nlohmann::json::array();
  for (const auto& t : tiles_) {
    std::string prev;
    bool sorted = true;
    for (const auto& [k, v] : t.rows) {
      if (!prev.empty() && k <= prev) {
        sorted = false;
        break;
      }
      prev = k;
    }
    tiles.push_back({{"id", t.id}, {"sorted_keys", sorted}});
  }
  return {{"tiles", tiles}, {"layout_generation", layout_gen_}};
}

}  // namespace ts
