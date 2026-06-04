#include "run_fetch.h"
#include "run_submit.h"
#include "run_train.h"

#include <cstring>
#include <iostream>

static int usage() {
  std::cerr << "usage: ratectl fetch|train|submit ...\n";
  return 2;
}

int main(int argc, char **argv) {
  if (argc < 2) return usage();
  if (std::strcmp(argv[1], "fetch") == 0) {
    return run_fetch_cmd(argc - 1, argv + 1);
  }
  if (std::strcmp(argv[1], "train") == 0) {
    return run_train_cmd(argc - 1, argv + 1);
  }
  if (std::strcmp(argv[1], "submit") == 0) {
    return run_submit_cmd(argc - 1, argv + 1);
  }
  return usage();
}
