#include "arc/http.hpp"

#include <curl/curl.h>
#include <stdexcept>

namespace arc {

namespace {

size_t write_cb(char* ptr, size_t size, size_t nmemb, void* userdata) {
  auto* buf = static_cast<std::string*>(userdata);
  buf->append(ptr, size * nmemb);
  return size * nmemb;
}

}  // namespace

std::string http_get(const std::string& url) {
  CURL* curl = curl_easy_init();
  if (!curl) {
    throw std::runtime_error("curl init failed");
  }
  std::string body;
  curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
  curl_easy_setopt(curl, CURLOPT_WRITEDATA, &body);
  curl_easy_setopt(curl, CURLOPT_TIMEOUT, 10L);
  CURLcode rc = curl_easy_perform(curl);
  long code = 0;
  curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &code);
  curl_easy_cleanup(curl);
  if (rc != CURLE_OK) {
    throw std::runtime_error("curl request failed");
  }
  if (code >= 400) {
    return "";
  }
  return body;
}

}  // namespace arc
