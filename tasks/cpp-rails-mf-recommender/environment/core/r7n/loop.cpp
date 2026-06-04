#include "loop.h"

#include "../m4t/pack.h"
#include "../../lib/fit_state.h"
#include "../../lib/json_min.h"

#include <cmath>
#include <cstdlib>
#include <fstream>
#include <sstream>

static std::vector<TrainRow> load_train(const std::string &manifest_path) {
  std::string dir = manifest_path.substr(0, manifest_path.find_last_of('/'));
  std::string train_path = dir + "/train.jsonl";
  std::ifstream in(train_path);
  std::vector<TrainRow> rows;
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    auto obj = json_min::parse(line);
    rows.push_back({static_cast<int>(obj.num("user_id")), static_cast<int>(obj.num("item_id")),
                    obj.num("score")});
  }
  return rows;
}

int phase_fit(const char *manifest_path, const char *pack_path) {
  auto man = json_min::parse(json_min::read_file(manifest_path));
  int n_users = static_cast<int>(man.num("n_users"));
  int n_items = static_cast<int>(man.num("n_items"));
  int n_factors = 8;
  uint32_t seed = 42;
  std::string train_sha = man.str_field("train_sha256");

  auto rows = load_train(manifest_path);
  FitState st;
  st.n_users = n_users;
  st.n_items = n_items;
  st.n_factors = n_factors;
  st.seed = seed;
  st.train_sha256 = train_sha;
  st.bu.assign(n_users, 0.0);
  st.bi.assign(n_items, 0.0);
  st.pu.assign(n_users, std::vector<double>(n_factors, 0.01));
  st.qi.assign(n_items, std::vector<double>(n_factors, 0.01));

  double sum = 0.0;
  for (const auto &r : rows) sum += r.score;
  st.global_mean = rows.empty() ? 0.0 : sum / rows.size();

  std::srand(seed);
  const int epochs = 12;
  const double lr = 0.08;
  const double reg = 0.02;
  for (int ep = 0; ep < epochs; ++ep) {
    for (const auto &r : rows) {
      int u = r.user_id - 1;
      int i = r.item_id - 1;
      double dot = 0.0;
      for (int f = 0; f < n_factors; ++f) dot += st.pu[u][f] * st.qi[i][f];
      double pred = st.global_mean + dot;
      double err = r.score - pred;
      for (int f = 0; f < n_factors; ++f) {
        double pu_old = st.pu[u][f];
        st.pu[u][f] += lr * (err * st.qi[i][f] - reg * st.pu[u][f]);
        st.qi[i][f] += lr * (err * pu_old - reg * st.qi[i][f]);
      }
    }
  }

  return step_q2(pack_path, &st);
}
