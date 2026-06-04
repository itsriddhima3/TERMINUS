#pragma once

#include <string>

std::string http_get(const std::string &url);
std::string http_post_json(const std::string &url, const std::string &body);
