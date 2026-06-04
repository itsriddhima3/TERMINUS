#include "run_fetch.h"

#include "../../client/k3p/pull.h"

#include <cstring>

int run_fetch_cmd(int argc, char **argv) {
  const char *base = "http://127.0.0.1:4567";
  const char *out = "/app/output/splits";
  for (int i = 1; i < argc; ++i) {
    if (std::strcmp(argv[i], "--base") == 0 && i + 1 < argc) base = argv[++i];
    if (std::strcmp(argv[i], "--out") == 0 && i + 1 < argc) out = argv[++i];
  }
  return op_fetch(base, out);
}
