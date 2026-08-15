#include "scene/serializer.h"

#include <fstream>

#include <nlohmann/json.hpp>

#include "audio/audio_source.h"
#include "core/logger.h"
#include "ecs/component.h"
#include "ecs/gameobject.h"
#include "physics/collider.h"
#include "physics/rigidbody.h"
#include "render/sprite_renderer.h"
#include "resource/resource_manager.h"
#include "scene/prefab.h"

namespace ge {
namespace serializer {

namespace {

using json = nlohmann::json;

std::vector<float> vec2_to_list(const Vec2& v) {
    return {v.x, v.y};
}

Vec2 list_to_vec2(const json& j) {
    if (j.is_array() && j.size() == 2) {
        return {j[0].get<float>(), j[1].get<float>()};
    }
    return {0.0f, 0.0f};
}

std::vector<float> vec4_to_list(const Vec4& v) {
    return {v.r, v.g, v.b, v.a};
}

Vec4 list_to_vec4(const json& j) {
    if (j.is_array() && j.size() == 4) {
        return {j[0].get<float>(), j[1].get<float>(), j[2].get<float>(), j[3].get<float>()};
    }
    return {1.0f, 1.0f, 1.0f, 1.0f};
}

std::vector<float> uv_to_list(const UvRect& uv) {
    return {uv.u0, uv.v0, uv.u1, uv.v1};
}

UvRect list_to_uv(const json& j) {
    if (j.is_array() && j.size() == 4) {
        return {j[0].get<float>(), j[1].get<float>(), j[2].get<float>(), j[3].get<float>()};
    }
    return {0.0f, 0.0f, 1.0f, 1.0f};
}

Texture* resolve_texture(const std::string& path) {
    ResourceManager& res = ResourceManager::instance();
    if (path == "builtin:white") {
        return res.builtin_white();
    }
    if (path == "builtin:circle") {
        return res.builtin_circle();
    }
    return res.load_texture(path);
}

std::string texture_path_of(Texture* texture) {
    ResourceManager& res = ResourceManager::instance();
    if (!texture) {
        return "";
    }
    if (texture == res.builtin_white()) {
        return "builtin:white";
    }
    if (texture == res.builtin_circle()) {
        return "builtin:circle";
    }
    return "";
}

void serialize_transform(const Transform& t, json& out) {
    out["pos"] = vec2_to_list(t.pos);
    out["rot"] = t.rot;
    out["scale"] = vec2_to_list(t.scale);
}

void deserialize_transform(Transform& t, const json& j) {
    if (j.contains("pos")) t.pos = list_to_vec2(j["pos"]);
    if (j.contains("rot")) t.rot = j["rot"].get<float>();
    if (j.contains("scale")) t.scale = list_to_vec2(j["scale"]);
}

void serialize_sprite(SpriteRenderer* spr, json& out) {
    out["texture"] = texture_path_of(spr->texture);
    out["uv"] = uv_to_list(spr->uv);
    out["color"] = vec4_to_list(spr->color);
    out["layer"] = spr->layer;
    out["sortOrder"] = spr->sort_order;
    out["interpolate"] = spr->interpolate;
}

void deserialize_sprite(SpriteRenderer* spr, const json& j) {
    if (j.contains("texture")) {
        const std::string path = j["texture"].get<std::string>();
        spr->texture = resolve_texture(path);
    }
    if (j.contains("uv")) spr->uv = list_to_uv(j["uv"]);
    if (j.contains("color")) spr->color = list_to_vec4(j["color"]);
    if (j.contains("layer")) spr->layer = j["layer"].get<int>();
    if (j.contains("sortOrder")) spr->sort_order = j["sortOrder"].get<int>();
    if (j.contains("interpolate")) spr->interpolate = j["interpolate"].get<bool>();
}

void serialize_rigidbody(RigidBody* rb, json& out) {
    out["velocity"] = vec2_to_list(rb->velocity);
    out["gravityScale"] = rb->gravity_scale;
    out["restitution"] = rb->restitution;
    out["mass"] = rb->mass;
    out["isStatic"] = rb->is_static;
    out["atRest"] = rb->at_rest;
}

void deserialize_rigidbody(RigidBody* rb, const json& j) {
    if (j.contains("velocity")) rb->velocity = list_to_vec2(j["velocity"]);
    if (j.contains("gravityScale")) rb->gravity_scale = j["gravityScale"].get<float>();
    if (j.contains("restitution")) rb->restitution = j["restitution"].get<float>();
    if (j.contains("mass")) rb->mass = j["mass"].get<float>();
    if (j.contains("isStatic")) rb->is_static = j["isStatic"].get<bool>();
    if (j.contains("atRest")) rb->at_rest = j["atRest"].get<bool>();
}

void serialize_circle(CircleCollider* col, json& out) {
    out["radius"] = col->radius;
    out["offset"] = vec2_to_list(col->offset);
}

void deserialize_circle(CircleCollider* col, const json& j) {
    if (j.contains("radius")) col->radius = j["radius"].get<float>();
    if (j.contains("offset")) col->offset = list_to_vec2(j["offset"]);
}

void serialize_box(BoxCollider* col, json& out) {
    out["size"] = vec2_to_list(col->size);
    out["offset"] = vec2_to_list(col->offset);
    out["oneWay"] = col->one_way;
}

void deserialize_box(BoxCollider* col, const json& j) {
    if (j.contains("size")) col->size = list_to_vec2(j["size"]);
    if (j.contains("offset")) col->offset = list_to_vec2(j["offset"]);
    if (j.contains("oneWay")) col->one_way = j["oneWay"].get<bool>();
}

void serialize_audio(AudioSource* src, json& out) {
    out["sound"] = src->sound;
    out["playOnCollision"] = src->play_on_collision;
    out["loop"] = src->loop;
    out["volume"] = src->volume;
    out["range"] = src->range;
    out["spatial"] = src->spatial;
}

void deserialize_audio(AudioSource* src, const json& j) {
    if (j.contains("sound")) src->sound = j["sound"].get<std::string>();
    if (j.contains("playOnCollision")) src->play_on_collision = j["playOnCollision"].get<bool>();
    if (j.contains("loop")) src->loop = j["loop"].get<bool>();
    if (j.contains("volume")) src->volume = j["volume"].get<float>();
    if (j.contains("range")) src->range = j["range"].get<float>();
    if (j.contains("spatial")) src->spatial = j["spatial"].get<bool>();
}

Component* factory(const std::string& type) {
    if (type == "SpriteRenderer") return new SpriteRenderer();
    if (type == "RigidBody") return new RigidBody();
    if (type == "CircleCollider") return new CircleCollider();
    if (type == "BoxCollider") return new BoxCollider();
    if (type == "AudioSource") return new AudioSource();
    return nullptr;
}

bool deserialize_component(Component* comp, const json& j) {
    if (auto* spr = dynamic_cast<SpriteRenderer*>(comp)) {
        deserialize_sprite(spr, j);
        return true;
    }
    if (auto* rb = dynamic_cast<RigidBody*>(comp)) {
        deserialize_rigidbody(rb, j);
        return true;
    }
    if (auto* col = dynamic_cast<CircleCollider*>(comp)) {
        deserialize_circle(col, j);
        return true;
    }
    if (auto* col = dynamic_cast<BoxCollider*>(comp)) {
        deserialize_box(col, j);
        return true;
    }
    if (auto* src = dynamic_cast<AudioSource*>(comp)) {
        deserialize_audio(src, j);
        return true;
    }
    return false;
}

}  // namespace

bool serialize_entity(GameObject* obj, json& out) {
    out["id"] = obj->name();
    out["name"] = obj->name();
    serialize_transform(obj->transform, out["transform"]);
    json components = json::array();
    for (Component* c : obj->components()) {
        json comp_json;
        if (auto* spr = dynamic_cast<SpriteRenderer*>(c)) {
            serialize_sprite(spr, comp_json);
            comp_json["type"] = "SpriteRenderer";
        } else if (auto* rb = dynamic_cast<RigidBody*>(c)) {
            serialize_rigidbody(rb, comp_json);
            comp_json["type"] = "RigidBody";
        } else if (auto* col = dynamic_cast<CircleCollider*>(c)) {
            serialize_circle(col, comp_json);
            comp_json["type"] = "CircleCollider";
        } else if (auto* col = dynamic_cast<BoxCollider*>(c)) {
            serialize_box(col, comp_json);
            comp_json["type"] = "BoxCollider";
        } else if (auto* src = dynamic_cast<AudioSource*>(c)) {
            serialize_audio(src, comp_json);
            comp_json["type"] = "AudioSource";
        } else {
            GE_LOG_WARN("serializer: skipping unknown component on '%s'", obj->name().c_str());
            continue;
        }
        components.push_back(comp_json);
    }
    out["components"] = components;
    return true;
}

GameObject* instantiate_entity(Scene& scene, const json& data) {
    std::string id = "entity";
    if (data.contains("id")) {
        id = data["id"].get<std::string>();
    }
    GameObject* obj = scene.CreateEntity(id);
    if (data.contains("transform")) {
        deserialize_transform(obj->transform, data["transform"]);
    }
    if (data.contains("components") && data["components"].is_array()) {
        for (const json& comp_json : data["components"]) {
            const std::string type = comp_json.value("type", "");
            Component* comp = factory(type);
            if (!comp) {
                GE_LOG_WARN("serializer: unknown component type '%s' on '%s'",
                            type.c_str(), id.c_str());
                continue;
            }
            obj->AddComponentRaw(comp);
            deserialize_component(comp, comp_json);
        }
    }
    return obj;
}

bool save_scene(const Scene& scene, const std::string& path) {
    json root;
    root["version"] = kSceneVersion;
    root["name"] = "scene";
    root["background"] = {0.08f, 0.09f, 0.12f};

    json entities = json::array();
    for (const GameObject* go : scene.entities()) {
        json entity;
        serialize_entity(const_cast<GameObject*>(go), entity);
        entities.push_back(entity);
    }
    root["entities"] = entities;

    std::ofstream file(path);
    if (!file.is_open()) {
        GE_LOG_ERROR("serializer: cannot write '%s'", path.c_str());
        return false;
    }
    file << root.dump(2);
    GE_LOG_INFO("serializer: saved scene with %zu entities to '%s'",
                entities.size(), path.c_str());
    return true;
}

bool load_scene(Scene& scene, const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        GE_LOG_ERROR("serializer: cannot open '%s'", path.c_str());
        return false;
    }
    json root;
    try {
        file >> root;
    } catch (const json::parse_error& e) {
        GE_LOG_ERROR("serializer: parse error in '%s': %s", path.c_str(), e.what());
        return false;
    }
    if (root.value("version", 0) != kSceneVersion) {
        GE_LOG_ERROR("serializer: unsupported scene version in '%s'", path.c_str());
        return false;
    }

    scene.clear();
    if (root.contains("entities") && root["entities"].is_array()) {
        for (const json& entity : root["entities"]) {
            if (entity.contains("prefab")) {
                const std::string prefab_path = entity["prefab"].get<std::string>();
                const json overrides = entity.value("overrides", json::object());
                prefab::instantiate(prefab_path, scene, entity.value("id", ""), overrides);
            } else {
                instantiate_entity(scene, entity);
            }
        }
    }
    GE_LOG_INFO("serializer: loaded scene from '%s' (%zu entities)",
                path.c_str(), scene.entities().size());
    return true;
}

}  // namespace serializer
}  // namespace ge
