#include "run_submit.h"

#include "../../core/p1v/submit.h"

#include <cstring>

int run_submit_cmd(int argc, char **argv) {
  const char *base = "http://127.0.0.1:4567";
  const char *pack = "/app/output/model/pack.bin";
  const char *receipt = "/app/output/submission/receipt.json";
  for (int i = 1; i < argc; ++i) {
    if (std::strcmp(argv[i], "--base") == 0 && i + 1 < argc) base = argv[++i];
    if (std::strcmp(argv[i], "--pack") == 0 && i + 1 < argc) pack = argv[++i];
    if (std::strcmp(argv[i], "--receipt") == 0 && i + 1 < argc) receipt = argv[++i];
  }
  return emit_v3(base, pack, receipt);
}
