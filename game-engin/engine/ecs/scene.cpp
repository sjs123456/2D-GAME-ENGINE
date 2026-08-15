#include "ecs/scene.h"

#include <algorithm>

#include "ecs/component.h"

namespace ge {

Scene::~Scene() {
    for (GameObject* g : entities_) {
        delete g;
    }
    entities_.clear();
}

GameObject* Scene::CreateEntity(const std::string& name) {
    auto* obj = new GameObject(name);
    entities_.push_back(obj);
    return obj;
}

void Scene::DestroyEntity(GameObject* obj) {
    obj->Destroy();
}

void Scene::DestroyEntityImmediate(GameObject* obj) {
    const auto it = std::find(entities_.begin(), entities_.end(), obj);
    if (it == entities_.end()) {
        return;
    }
    delete obj;
    entities_.erase(it);
}

GameObject* Scene::FindByName(const std::string& name) const {
    for (GameObject* g : entities_) {
        if (g->name() == name) {
            return g;
        }
    }
    return nullptr;
}

void Scene::Update(float dt) {
    for (GameObject* g : entities_) {
        if (!g->active() || g->pending_destroy()) {
            continue;
        }
        for (Component* c : g->components()) {
            if (c->is_active()) {
                c->OnUpdate(dt);
            }
        }
    }
    RemoveDestroyed();
}

void Scene::Render(float alpha) {
    for (GameObject* g : entities_) {
        if (!g->active() || g->pending_destroy()) {
            continue;
        }
        for (Component* c : g->components()) {
            if (c->is_active()) {
                c->OnRender(alpha);
            }
        }
    }
}

void Scene::RemoveDestroyed() {
    const auto new_end = std::remove_if(entities_.begin(), entities_.end(),
                                        [](GameObject* g) {
                                            if (g->pending_destroy()) {
                                                delete g;
                                                return true;
                                            }
                                            return false;
                                        });
    entities_.erase(new_end, entities_.end());
}

void Scene::clear() {
    for (GameObject* g : entities_) {
        delete g;
    }
    entities_.clear();
    ++generation_;
}

}  // namespace ge
