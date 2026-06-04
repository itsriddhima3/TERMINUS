#include <map>
#include <string>

namespace vx {
namespace decoy {

std::map<std::string, std::string> blob_cache;

const std::string& memo(const std::string& key, const std::string& value) {
    auto it = blob_cache.find(key);
    if (it != blob_cache.end()) {
        return it->second;
    }
    return blob_cache.emplace(key, value).first->second;
}

}  // namespace decoy
}  // namespace vx
