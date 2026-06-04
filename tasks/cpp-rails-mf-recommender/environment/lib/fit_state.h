#pragma once

#include <cstdint>
#include <string>
#include <vector>

struct TrainRow {
  int user_id;
  int item_id;
  double score;
};

struct FitState {
  int n_users = 0;
  int n_items = 0;
  int n_factors = 8;
  uint32_t seed = 42;
  double global_mean = 0.0;
  std::string train_sha256;
  std::vector<double> bu;
  std::vector<double> bi;
  std::vector<std::vector<double>> pu;
  std::vector<std::vector<double>> qi;
};
