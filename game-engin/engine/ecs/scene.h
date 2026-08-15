#pragma once

#include <string>
#include <vector>

#include "ecs/gameobject.h"

namespace ge {

class Scene {
public:
    Scene() = default;
    ~Scene();
    Scene(const Scene&) = delete;
    Scene& operator=(const Scene&) = delete;

    GameObject* CreateEntity(const std::string& name);
    void DestroyEntity(GameObject* obj);
    void DestroyEntityImmediate(GameObject* obj);
    GameObject* FindByName(const std::string& name) const;

    void Update(float dt);
    void Render(float alpha);
    void RemoveDestroyed();
    void clear();
    unsigned int generation() const { return generation_; }

    std::vector<GameObject*>& entities() { return entities_; }
    const std::vector<GameObject*>& entities() const { return entities_; }

private:
    std::vector<GameObject*> entities_;
    unsigned int generation_ = 0;
};

}  // namespace ge
