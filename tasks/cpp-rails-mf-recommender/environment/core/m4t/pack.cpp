#include "pack.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <vector>

static void write_u32(std::vector<uint8_t> &buf, uint32_t v) {
  buf.push_back(static_cast<uint8_t>(v));
  buf.push_back(static_cast<uint8_t>(v >> 8));
  buf.push_back(static_cast<uint8_t>(v >> 16));
  buf.push_back(static_cast<uint8_t>(v >> 24));
}

static void write_f32(std::vector<uint8_t> &buf, float v) {
  uint32_t bits;
  std::memcpy(&bits, &v, 4);
  write_u32(buf, bits);
}

int step_q2(const char *path, const FitState *st) {
  std::vector<uint8_t> out;
  out.insert(out.end(), {'R', 'T', 'P', 'K'});
  write_u32(out, 1);
  write_u32(out, st->seed);
  write_u32(out, static_cast<uint32_t>(st->n_users));
  write_u32(out, static_cast<uint32_t>(st->n_items));
  write_u32(out, static_cast<uint32_t>(st->n_factors));
  write_f32(out, static_cast<float>(st->global_mean));

  for (char c : st->train_sha256.substr(0, 16)) {
    out.push_back(static_cast<uint8_t>(c));
  }

  for (double v : st->bu) write_f32(out, static_cast<float>(v));
  for (double v : st->bi) write_f32(out, static_cast<float>(v));

  double global_max = 0.0;
  for (const auto &row : st->pu) {
    for (double v : row) global_max = std::max(global_max, std::abs(v));
  }
  for (const auto &row : st->qi) {
    for (double v : row) global_max = std::max(global_max, std::abs(v));
  }
  float scale = global_max > 0 ? static_cast<float>(global_max / 127.0) : 1.0f;
  write_f32(out, scale);

  for (const auto &row : st->pu) {
    for (double v : row) {
      int8_t q = static_cast<int8_t>(std::lround(v / scale));
      out.push_back(static_cast<uint8_t>(q));
    }
  }
  for (const auto &row : st->qi) {
    for (double v : row) {
      int8_t q = static_cast<int8_t>(std::lround(v / scale));
      out.push_back(static_cast<uint8_t>(q));
    }
  }

  std::ofstream f(path, std::ios::binary);
  f.write(reinterpret_cast<const char *>(out.data()), static_cast<std::streamsize>(out.size()));
  return 0;
}
