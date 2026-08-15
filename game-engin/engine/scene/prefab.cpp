#include "scene/prefab.h"

#include <fstream>
#include <sstream>

#include <nlohmann/json.hpp>

#include "core/logger.h"
#include "resource/resource_manager.h"
#include "scene/serializer.h"

namespace ge {
namespace prefab {

namespace {
using json = nlohmann::json;

json* navigate(json& root, const std::string& path, bool create) {
    json* current = &root;
    std::istringstream iss(path);
    std::string token;
    while (std::getline(iss, token, '.')) {
        size_t bracket = token.find('[');
        const std::string key = token.substr(0, bracket);
        const bool has_index = bracket != std::string::npos;

        if (!key.empty()) {
            if (!current->is_object()) {
                return nullptr;
            }
            if (!current->contains(key)) {
                if (!create) {
                    return nullptr;
                }
                (*current)[key] = json::object();
            }
            current = &(*current)[key];
        }
        if (has_index) {
            const size_t close = token.find(']', bracket);
            if (close == std::string::npos || !current->is_array()) {
                return nullptr;
            }
            const int index = std::stoi(token.substr(bracket + 1, close - bracket - 1));
            if (index < 0 || index >= static_cast<int>(current->size())) {
                return nullptr;
            }
            current = &(*current)[index];
        }
    }
    return current;
}
}  // namespace

bool instantiate(const std::string& prefab_path, Scene& scene,
                 const std::string& instance_id, const json& overrides) {
    const std::string& root = ResourceManager::instance().asset_root();
    const std::string full_path = prefab_path.rfind(root, 0) == 0
                                      ? prefab_path
                                      : root + "/" + prefab_path;
    std::ifstream file(full_path);
    if (!file.is_open()) {
        GE_LOG_ERROR("prefab: cannot open '%s'", full_path.c_str());
        return false;
    }
    json data;
    try {
        file >> data;
    } catch (const json::parse_error& e) {
        GE_LOG_ERROR("prefab: parse error in '%s': %s", prefab_path.c_str(), e.what());
        return false;
    }

    if (!instance_id.empty()) {
        data["id"] = instance_id;
        data["name"] = instance_id;
    }

    for (auto it = overrides.begin(); it != overrides.end(); ++it) {
        json* target = navigate(data, it.key(), true);
        if (target) {
            *target = it.value();
        } else {
            GE_LOG_WARN("prefab: override path '%s' not applied", it.key().c_str());
        }
    }

    GameObject* obj = serializer::instantiate_entity(scene, data);
    GE_LOG_INFO("prefab: instantiated '%s' from '%s'", instance_id.c_str(), prefab_path.c_str());
    (void)obj;
    return true;
}

}  // namespace prefab
}  // namespace ge
