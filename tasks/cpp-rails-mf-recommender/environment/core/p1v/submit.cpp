#include "submit.h"

#include "../../lib/fit_state.h"
#include "../../lib/http_util.h"
#include "../../lib/json_min.h"

#include <cmath>
#include <cstring>
#include <fstream>
#include <sstream>
#include <vector>

struct LoadedPack {
  FitState st;
  float global_scale = 1.0f;
  std::vector<int8_t> pu_q;
  std::vector<int8_t> qi_q;
};

static LoadedPack load_pack(const char *path) {
  std::ifstream in(path, std::ios::binary);
  std::vector<uint8_t> buf((std::istreambuf_iterator<char>(in)), {});
  LoadedPack lp;
  size_t off = 4;
  off += 4;
  auto u32 = [&](size_t &o) {
    uint32_t v = buf[o] | (buf[o + 1] << 8) | (buf[o + 2] << 16) | (buf[o + 3] << 24);
    o += 4;
    return v;
  };
  lp.st.seed = u32(off);
  lp.st.n_users = static_cast<int>(u32(off));
  lp.st.n_items = static_cast<int>(u32(off));
  lp.st.n_factors = static_cast<int>(u32(off));
  float mean;
  std::memcpy(&mean, &buf[off], 4);
  off += 4;
  lp.st.global_mean = mean;
  lp.st.train_sha256.assign(reinterpret_cast<char *>(&buf[off]), 16);
  off += 16;
  lp.st.bu.resize(lp.st.n_users);
  lp.st.bi.resize(lp.st.n_items);
  for (int i = 0; i < lp.st.n_users; ++i) {
    std::memcpy(&lp.st.bu[i], &buf[off], 4);
    off += 4;
  }
  for (int i = 0; i < lp.st.n_items; ++i) {
    std::memcpy(&lp.st.bi[i], &buf[off], 4);
    off += 4;
  }
  std::memcpy(&lp.global_scale, &buf[off], 4);
  off += 4;
  int pu_len = lp.st.n_users * lp.st.n_factors;
  int qi_len = lp.st.n_items * lp.st.n_factors;
  lp.pu_q.resize(pu_len);
  lp.qi_q.resize(qi_len);
  for (int i = 0; i < pu_len; ++i) lp.pu_q[i] = static_cast<int8_t>(buf[off++]);
  for (int i = 0; i < qi_len; ++i) lp.qi_q[i] = static_cast<int8_t>(buf[off++]);
  lp.st.pu.assign(lp.st.n_users, std::vector<double>(lp.st.n_factors));
  lp.st.qi.assign(lp.st.n_items, std::vector<double>(lp.st.n_factors));
  for (int u = 0; u < lp.st.n_users; ++u) {
    for (int f = 0; f < lp.st.n_factors; ++f) {
      lp.st.pu[u][f] = lp.pu_q[u * lp.st.n_factors + f] * lp.global_scale;
    }
  }
  for (int i = 0; i < lp.st.n_items; ++i) {
    for (int f = 0; f < lp.st.n_factors; ++f) {
      lp.st.qi[i][f] = lp.qi_q[i * lp.st.n_factors + f] * lp.global_scale;
    }
  }
  return lp;
}

static double score_pair(const LoadedPack &lp, int user_id, int item_id) {
  int u = user_id - 1;
  int i = item_id - 1;
  double dot = 0.0;
  for (int f = 0; f < lp.st.n_factors; ++f) dot += lp.st.pu[u][f] * lp.st.qi[i][f];
  return lp.st.global_mean + dot;
}

int emit_v3(const char *base, const char *pack_path, const char *receipt_path) {
  {
    std::ifstream probe(pack_path, std::ios::binary);
    if (!probe.good()) return 1;
  }
  auto lp = load_pack(pack_path);
  std::string hold_url = std::string(base) + "/api/v1/holdout";
  auto hold = json_min::parse(http_get(hold_url));
  auto pairs = hold.array("pairs");

  std::ostringstream body;
  body << "{\"items\":[";
  bool first = true;
  for (const auto &p : pairs) {
    if (!first) body << ',';
    first = false;
    int uid = static_cast<int>(p.num("user_id"));
    int iid = static_cast<int>(p.num("item_id"));
    double sc = score_pair(lp, uid, iid);
    body << "{\"user_id\":" << uid << ",\"item_id\":" << iid << ",\"score\":" << sc << "}";
  }
  body << "]}";

  std::string post_url = std::string(base) + "/api/v1/predictions";
  auto resp = json_min::parse(http_post_json(post_url, body.str()));

  std::ostringstream receipt;
  receipt << "{"
          << "\"schema_version\":1,"
          << "\"accepted\":" << (resp.num("accepted") > 0.5 ? "true" : "false") << ","
          << "\"rmse\":" << resp.num("rmse") << ","
          << "\"n_scored\":" << static_cast<int>(resp.num("n_scored"))
          << "}";
  std::ofstream out(receipt_path);
  out << receipt.str();
  return 0;
}
