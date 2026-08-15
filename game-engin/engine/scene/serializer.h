#pragma once

#include <string>

#include <nlohmann/json.hpp>

#include "ecs/scene.h"

namespace ge {

namespace serializer {
constexpr int kSceneVersion = 1;

bool save_scene(const Scene& scene, const std::string& path);
bool load_scene(Scene& scene, const std::string& path);
bool serialize_entity(GameObject* obj, nlohmann::json& out);
GameObject* instantiate_entity(Scene& scene, const nlohmann::json& data);
}  // namespace serializer

}  // namespace ge
