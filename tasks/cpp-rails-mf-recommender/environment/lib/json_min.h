#pragma once

#include <cctype>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace json_min {

struct Value {
  enum Kind { kNull, kNum, kStr, kArr, kObj } kind = kNull;
  double number = 0.0;
  std::string str;
  std::vector<Value> arr;
  std::unordered_map<std::string, Value> obj;

  double num(const std::string &k) const {
    auto it = obj.find(k);
    if (it == obj.end()) return 0.0;
    return it->second.number;
  }
  std::string str_field(const std::string &k) const {
    auto it = obj.find(k);
    if (it == obj.end()) return "";
    return it->second.str;
  }
  const std::vector<Value> &array(const std::string &k) const {
    static const std::vector<Value> empty;
    auto it = obj.find(k);
    if (it == obj.end()) return empty;
    return it->second.arr;
  }
};

inline void sha256(const char *data, size_t len, unsigned char out[32]);

inline std::string read_file(const std::string &path) {
  std::ifstream in(path);
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

inline size_t skip_ws(const std::string &s, size_t i) {
  while (i < s.size() && (s[i] == ' ' || s[i] == '\n' || s[i] == '\r' || s[i] == '\t')) ++i;
  return i;
}

inline Value parse_value(const std::string &s, size_t &i);

inline Value parse_string(const std::string &s, size_t &i) {
  Value v;
  v.kind = Value::kStr;
  ++i;
  while (i < s.size() && s[i] != '"') {
    if (s[i] == '\\') ++i;
    if (i < s.size()) v.str.push_back(s[i++]);
  }
  if (i < s.size()) ++i;
  return v;
}

inline Value parse_number(const std::string &s, size_t &i) {
  Value v;
  v.kind = Value::kNum;
  size_t start = i;
  while (i < s.size() && (std::isdigit(static_cast<unsigned char>(s[i])) || s[i] == '.' || s[i] == '-' ||
                           s[i] == 'e' || s[i] == 'E' || s[i] == '+')) {
    ++i;
  }
  v.number = std::stod(s.substr(start, i - start));
  return v;
}

inline Value parse_array(const std::string &s, size_t &i) {
  Value v;
  v.kind = Value::kArr;
  ++i;
  i = skip_ws(s, i);
  if (i < s.size() && s[i] == ']') {
    ++i;
    return v;
  }
  while (i < s.size()) {
    v.arr.push_back(parse_value(s, i));
    i = skip_ws(s, i);
    if (i < s.size() && s[i] == ',') {
      ++i;
      i = skip_ws(s, i);
      continue;
    }
    if (i < s.size() && s[i] == ']') {
      ++i;
      break;
    }
  }
  return v;
}

inline Value parse_object(const std::string &s, size_t &i) {
  Value v;
  v.kind = Value::kObj;
  ++i;
  i = skip_ws(s, i);
  if (i < s.size() && s[i] == '}') {
    ++i;
    return v;
  }
  while (i < s.size()) {
    i = skip_ws(s, i);
    auto key = parse_string(s, i).str;
    i = skip_ws(s, i);
    if (i < s.size() && s[i] == ':') ++i;
    i = skip_ws(s, i);
    v.obj[key] = parse_value(s, i);
    i = skip_ws(s, i);
    if (i < s.size() && s[i] == ',') {
      ++i;
      continue;
    }
    if (i < s.size() && s[i] == '}') {
      ++i;
      break;
    }
  }
  return v;
}

inline Value parse_literal(const std::string &s, size_t &i) {
  Value v;
  v.kind = Value::kNum;
  if (s.compare(i, 4, "true") == 0) {
    v.number = 1.0;
    i += 4;
    return v;
  }
  if (s.compare(i, 5, "false") == 0) {
    v.number = 0.0;
    i += 5;
    return v;
  }
  return {};
}

inline Value parse_value(const std::string &s, size_t &i) {
  i = skip_ws(s, i);
  if (i >= s.size()) return {};
  char c = s[i];
  if (c == '"') return parse_string(s, i);
  if (c == '{') return parse_object(s, i);
  if (c == '[') return parse_array(s, i);
  if (c == '-' || std::isdigit(static_cast<unsigned char>(c))) return parse_number(s, i);
  if (c == 't' || c == 'f') return parse_literal(s, i);
  return {};
}

inline Value parse(const std::string &s) {
  size_t i = 0;
  return parse_value(s, i);
}

inline double num(const Value &v, const std::string &k) { return v.num(k); }
inline std::string str(const Value &v, const std::string &k) { return v.str_field(k); }
inline const std::vector<Value> &array(const Value &v, const std::string &k) { return v.array(k); }

}  // namespace json_min

#include "sha256_impl.inc"
