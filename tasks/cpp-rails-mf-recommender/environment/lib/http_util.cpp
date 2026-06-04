#include "http_util.h"

#include <curl/curl.h>
#include <stdexcept>
#include <sstream>

namespace {

size_t write_cb(char *ptr, size_t size, size_t nmemb, void *userdata) {
  auto *out = static_cast<std::string *>(userdata);
  out->append(ptr, size * nmemb);
  return size * nmemb;
}

std::string do_request(const std::string &url, const char *method, const std::string *body) {
  CURL *curl = curl_easy_init();
  if (!curl) {
    throw std::runtime_error("curl init failed");
  }
  std::string response;
  curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_cb);
  curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
  curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
  if (body) {
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body->c_str());
    struct curl_slist *headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, method);
    CURLcode rc = curl_easy_perform(curl);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    if (rc != CURLE_OK) {
      throw std::runtime_error("curl failed");
    }
    return response;
  }
  curl_easy_setopt(curl, CURLOPT_HTTPGET, 1L);
  CURLcode rc = curl_easy_perform(curl);
  curl_easy_cleanup(curl);
  if (rc != CURLE_OK) {
    throw std::runtime_error("curl failed");
  }
  return response;
}

}  // namespace

std::string http_get(const std::string &url) { return do_request(url, "GET", nullptr); }

std::string http_post_json(const std::string &url, const std::string &body) {
  return do_request(url, "POST", &body);
}
