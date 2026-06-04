#include "pull.h"

#include "../../lib/http_util.h"
#include "../../lib/json_min.h"

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>

namespace fs = std::filesystem;

static std::string sha256_hex(const std::string &data) {
  unsigned char digest[32];
  json_min::sha256(data.data(), data.size(), digest);
  std::ostringstream oss;
  for (int i = 0; i < 32; ++i) {
    oss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(digest[i]);
  }
  return oss.str();
}

int op_fetch(const char *base, const char *out_dir) {
  fs::create_directories(out_dir);
  std::string split_url = std::string(base) + "/api/v1/split";
  auto split_doc = json_min::parse(http_get(split_url));

  int n_train = static_cast<int>(split_doc.num("n_train"));
  int per_page = static_cast<int>(split_doc.num("per_page"));
  int total_pages = n_train / per_page;

  std::ostringstream train_body;
  int page = 1;
  while (page <= total_pages) {
    std::ostringstream url;
    url << base << "/api/v1/train_ratings?page=" << page << "&per_page=" << per_page;
    auto page_doc = json_min::parse(http_get(url.str()));
    auto rows = page_doc.array("rows");
    for (const auto &row : rows) {
      train_body << "{\"user_id\":" << static_cast<int>(row.num("user_id"))
                 << ",\"item_id\":" << static_cast<int>(row.num("item_id"))
                 << ",\"score\":" << row.num("score") << "}\n";
    }
    page += 1;
  }

  std::string train_str = train_body.str();
  std::string manifest_path = std::string(out_dir) + "/manifest.json";
  std::string train_path = std::string(out_dir) + "/train.jsonl";

  std::ofstream train_out(train_path);
  train_out << train_str;
  train_out.close();

  std::ostringstream manifest;
  manifest << "{"
           << "\"schema_version\":1,"
           << "\"split_id\":\"" << split_doc.str_field("split_id") << "\","
           << "\"n_users\":" << static_cast<int>(split_doc.num("n_users")) << ","
           << "\"n_items\":" << static_cast<int>(split_doc.num("n_items")) << ","
           << "\"n_train\":" << n_train << ","
           << "\"train_sha256\":\"" << sha256_hex(train_str) << "\","
           << "\"fit_seed\":" << static_cast<int>(split_doc.num("fit_seed")) << ","
           << "\"n_factors\":" << static_cast<int>(split_doc.num("n_factors")) << ","
           << "\"fit_epochs\":" << static_cast<int>(split_doc.num("fit_epochs")) << ","
           << "\"lr_base\":" << split_doc.num("lr_base") << ","
           << "\"lr_decay\":" << split_doc.num("lr_decay")
           << "}";
  std::ofstream man_out(manifest_path);
  man_out << manifest.str();
  man_out.close();
  return 0;
}
