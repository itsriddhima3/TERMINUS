#include "codec.h"

std::string b64_encode_diag(const std::string &raw) {
  static const char *tbl =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  std::string out;
  for (size_t i = 0; i < raw.size(); i += 3) {
    unsigned val = static_cast<unsigned char>(raw[i]) << 16;
    if (i + 1 < raw.size()) val |= static_cast<unsigned char>(raw[i + 1]) << 8;
    if (i + 2 < raw.size()) val |= static_cast<unsigned char>(raw[i + 2]);
    out.push_back(tbl[(val >> 18) & 63]);
    out.push_back(tbl[(val >> 12) & 63]);
    out.push_back(i + 1 < raw.size() ? tbl[(val >> 6) & 63] : '=');
    out.push_back(i + 2 < raw.size() ? tbl[val & 63] : '=');
  }
  return out;
}
