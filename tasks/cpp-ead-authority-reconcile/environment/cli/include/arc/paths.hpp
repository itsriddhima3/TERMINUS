#pragma once

#include <filesystem>
#include <fstream>
#include <string>

namespace arc {

inline std::filesystem::path app_root() { return "/app"; }

inline std::filesystem::path var_dir() { return app_root() / "var"; }

inline std::filesystem::path output_dir() { return app_root() / "output"; }

inline std::filesystem::path ead_root() { return app_root() / "data" / "ead"; }

inline std::filesystem::path config_dir() { return app_root() / "config"; }

inline std::string read_text_file(const std::filesystem::path& p) {
  std::ifstream in(p);
  return std::string((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
}

}  // namespace arc
