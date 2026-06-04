#include "run_train.h"

#include "../../core/r7n/loop.h"

#include <cstring>

int run_train_cmd(int argc, char **argv) {
  const char *manifest = "/app/output/splits/manifest.json";
  const char *pack = "/app/output/model/pack.bin";
  for (int i = 1; i < argc; ++i) {
    if (std::strcmp(argv[i], "--manifest") == 0 && i + 1 < argc) manifest = argv[++i];
    if (std::strcmp(argv[i], "--pack") == 0 && i + 1 < argc) pack = argv[++i];
  }
  return phase_fit(manifest, pack);
}
