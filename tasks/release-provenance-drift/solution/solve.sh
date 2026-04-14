#!/usr/bin/env bash
set -euo pipefail

cd /app

cat > /app/plugin-core/build.rs <<'RS'
use sha2::{Digest, Sha256};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

fn update_with_file(hasher: &mut Sha256, label: &str, path: &Path) {
    let bytes = fs::read(path).unwrap_or_else(|err| panic!("read {label}: {err}"));
    hasher.update(label.as_bytes());
    hasher.update([0]);
    hasher.update(&bytes);
    hasher.update([0xff]);
}

fn main() {
    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR"));
    let out_dir = PathBuf::from(env::var("OUT_DIR").expect("OUT_DIR"));
    let tpl_path = manifest_dir.join("../codegen/templates/ffi.rs.tpl");
    let lib_rs_path = manifest_dir.join(format!("src/lib{}", ".rs"));
    let layout_path = manifest_dir.join(format!("../stage_graph/stage_{}", "layout.json"));

    for path in [&tpl_path, &lib_rs_path, &layout_path] {
        println!("cargo:rerun-if-changed={}", path.display());
    }

    let tpl = fs::read_to_string(&tpl_path).expect("read template");
    let mut hasher = Sha256::new();
    update_with_file(&mut hasher, "ffi.rs.tpl", &tpl_path);
    update_with_file(&mut hasher, concat!("lib", ".rs"), &lib_rs_path);
    update_with_file(&mut hasher, concat!("stage_layout", ".json"), &layout_path);
    let full = format!("{:x}", hasher.finalize());
    let epoch: String = full.chars().take(24).collect();

    let generated = tpl.replace("@@EPOCH@@", &epoch);
    let gen_dir = out_dir.join("generated");
    fs::create_dir_all(&gen_dir).expect("mkdir generated");
    fs::write(gen_dir.join("ffi.rs"), generated).expect("write ffi.rs");
    fs::write(out_dir.join("prov_epoch.txt"), format!("{epoch}\n")).expect("write epoch");
}
RS

python3 - <<'PY'
from pathlib import Path

files = {
    Path('/app/stage_graph/stage_rust.sh'): '''#!/bin/bash
set -euo pipefail
# shellcheck source=/dev/null
source "$(dirname "$0")/env.sh"
mkdir -p "${STAGE_ROOT}/bin"
td="${CARGO_TARGET_DIR}"
case "${PROFILE}" in
  release) src="${td}/release/libplugin_core.so" ;;
  *) src="${td}/debug/libplugin_core.so" ;;
esac
install -m0755 "$src" "${STAGE_ROOT}/bin/libplugin_core.so"
''',
    Path('/app/stage_graph/stage_cpp.sh'): '''#!/bin/bash
set -euo pipefail
# shellcheck source=/dev/null
source "$(dirname "$0")/env.sh"
mkdir -p "${STAGE_ROOT}/bin"
layout_path="$(dirname "$0")/stage_""layout.json"
python3 - "$layout_path" "$PROFILE" "$CMAKE_BUILD_DIR" "$STAGE_ROOT" <<'INNER'
import json
import shutil
import sys
from pathlib import Path
layout_path = Path(sys.argv[1])
profile = sys.argv[2]
build_dir = Path(sys.argv[3])
stage_bin = Path(sys.argv[4]) / 'bin'
layout = json.loads(layout_path.read_text(encoding='utf-8'))
stage_bin.mkdir(parents=True, exist_ok=True)
for name in layout[profile]['cpp']:
    src = build_dir / name
    if not src.is_file():
        raise SystemExit(f'missing {src}')
    shutil.copy2(src, stage_bin / name)
INNER
''',
    Path('/app/ship_seal/package.sh'): r'''#!/bin/bash
set -euo pipefail
# shellcheck source=/dev/null
source /app/stage_graph/env.sh
mkdir -p "${PKG_ROOT}/bin"
rm -f "${PKG_ROOT}/bin/"*
cp -a "${STAGE_ROOT}/bin/." "${PKG_ROOT}/bin/"
epoch_file="$(python3 - "$CARGO_TARGET_DIR" "$PROFILE" <<'INNER'
import sys
from pathlib import Path

target_dir = Path(sys.argv[1])
profile = sys.argv[2]
candidates = sorted(
    (target_dir / profile / 'build').glob('**/prov_epoch.txt'),
    key=lambda p: p.stat().st_mtime_ns,
)
if not candidates:
    raise SystemExit(f'missing prov_epoch.txt for {profile}')
print(candidates[-1])
INNER
)"
epoch="$(tr -d '\n' < "$epoch_file")"
python3 - "$PKG_ROOT/seal.json" "$epoch" "${PKG_ROOT}/bin" <<'INNER'
import hashlib
import json
import os
import sys
from pathlib import Path

out_path, epoch, bin_root = sys.argv[1], sys.argv[2].strip(), sys.argv[3]
files = {}
for name in sorted(os.listdir(bin_root)):
    candidate = Path(bin_root) / name
    if candidate.is_file():
        files[name] = hashlib.sha256(candidate.read_bytes()).hexdigest()
payload = {'epoch': epoch, 'files': files}
out = Path(out_path)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, sort_keys=True) + '\n', encoding='utf-8')
INNER
''',
    Path('/app/loader/load.c'): r'''#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "inval_policy.c"

static char *slurp(const char *path) {
  FILE *f = fopen(path, "rb");
  long sz;
  char *buf;
  if (!f) {
    return NULL;
  }
  fseek(f, 0, SEEK_END);
  sz = ftell(f);
  fseek(f, 0, SEEK_SET);
  buf = malloc((size_t)sz + 1);
  if (!buf) {
    fclose(f);
    return NULL;
  }
  if (sz > 0) {
    fread(buf, 1, (size_t)sz, f);
  }
  buf[sz] = 0;
  fclose(f);
  return buf;
}

static int extract_json_string(const char *json, const char *key, char *out, size_t outsz) {
  const char *cursor = strstr(json, key);
  size_t i = 0;
  if (!cursor) {
    return -1;
  }
  cursor = strchr(cursor, ':');
  if (!cursor) {
    return -1;
  }
  cursor = strchr(cursor, '"');
  if (!cursor) {
    return -1;
  }
  cursor++;
  while (cursor[i] && cursor[i] != '"' && i + 1 < outsz) {
    out[i] = cursor[i];
    i++;
  }
  out[i] = 0;
  return 0;
}

static int extract_file_hash_json(const char *json, const char *name, char *out, size_t outsz) {
  char key[256];
  if (snprintf(key, sizeof key, "\"%s\"", name) >= (int)sizeof key) {
    return -1;
  }
  return extract_json_string(json, key, out, outsz);
}

static const char *basename_c(const char *path) {
  const char *slash = strrchr(path, '/');
  return slash ? slash + 1 : path;
}

static int sha256sum_hex(const char *path, char *out, size_t outsz) {
  char cmd[1024];
  FILE *pipe;
  if (strchr(path, '\'')) {
    return -1;
  }
  if (snprintf(cmd, sizeof cmd, "sha256sum -- '%s'", path) >= (int)sizeof cmd) {
    return -1;
  }
  pipe = popen(cmd, "r");
  if (!pipe) {
    return -1;
  }
  if (!fgets(out, (int)outsz, pipe)) {
    pclose(pipe);
    return -1;
  }
  pclose(pipe);
  for (size_t i = 0; out[i]; ++i) {
    if (out[i] == ' ' || out[i] == '\t' || out[i] == '\n') {
      out[i] = 0;
      break;
    }
  }
  return 0;
}

int main(int argc, char **argv) {
  const char *so = argc > 1 ? argv[1] : "/app/out/pkg/bin/libplugin_core.so";
  const char *seal = argc > 2 ? argv[2] : "/app/out/pkg/seal.json";
  char *js;
  char want_epoch[128];
  char want_hash[128];
  char actual_hash[128];
  void *h;
  const char *(*ep)(void);
  size_t (*eln)(void);

  js = slurp(seal);
  if (!js) {
    fprintf(stderr, "cannot read seal\n");
    return 2;
  }
  if (extract_json_string(js, "\"epoch\"", want_epoch, sizeof want_epoch) != 0) {
    free(js);
    fprintf(stderr, "bad seal\n");
    return 3;
  }
  if (extract_file_hash_json(js, basename_c(so), want_hash, sizeof want_hash) != 0) {
    free(js);
    fprintf(stderr, "missing file hash\n");
    return 8;
  }
  free(js);

  if (!cache_still_valid(so, seal)) {
    fprintf(stderr, "cache invalid\n");
    return 4;
  }
  if (sha256sum_hex(so, actual_hash, sizeof actual_hash) != 0) {
    fprintf(stderr, "hash read failed\n");
    return 9;
  }
  if (strcmp(actual_hash, want_hash) != 0) {
    fprintf(stderr, "hash mismatch\n");
    return 10;
  }

  h = dlopen(so, RTLD_NOW);
  if (!h) {
    fprintf(stderr, "dlopen: %s\n", dlerror());
    return 5;
  }
  ep = (const char *(*)(void))dlsym(h, "plugin_epoch");
  eln = (size_t (*)(void))dlsym(h, "plugin_epoch_len");
  if (!ep || !eln) {
    fprintf(stderr, "missing exports\n");
    return 6;
  }
  {
    const char *got = ep();
    size_t n = eln();
    size_t wn = strlen(want_epoch);
    if (n != wn || strncmp(got, want_epoch, n) != 0) {
      fprintf(stderr, "epoch mismatch\n");
      return 7;
    }
  }
  dlclose(h);
  return 0;
}
''',
    Path('/app/loader/inval_policy.c'): '''#include <sys/stat.h>

int cache_still_valid(const char *plugin_path, const char *seal_path) {
  struct stat plugin_stat;
  struct stat seal_stat;
  if (!plugin_path || !seal_path) {
    return 0;
  }
  if (stat(plugin_path, &plugin_stat) != 0) {
    return 0;
  }
  if (stat(seal_path, &seal_stat) != 0) {
    return 0;
  }
  return 1;
}
''',
}

for path, content in files.items():
    path.write_text(content, encoding='utf-8')

for path in (
    Path('/app/stage_graph/stage_rust.sh'),
    Path('/app/stage_graph/stage_cpp.sh'),
    Path('/app/ship_seal/package.sh'),
):
    path.chmod(0o755)
PY
