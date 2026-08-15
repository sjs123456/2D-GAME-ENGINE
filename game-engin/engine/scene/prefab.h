#pragma once

#include <string>

#include <nlohmann/json.hpp>

#include "ecs/scene.h"

namespace ge {

namespace prefab {

bool instantiate(const std::string& prefab_path, Scene& scene,
                 const std::string& instance_id,
                 const nlohmann::json& overrides = nlohmann::json::object());

}  // namespace prefab

}  // namespace ge
