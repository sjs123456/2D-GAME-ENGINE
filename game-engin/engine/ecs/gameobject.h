#pragma once

#include <algorithm>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

#include "core/math.h"
#include "ecs/component.h"

namespace ge {

struct Transform {
    Vec2 pos{0.0f, 0.0f};
    float rot = 0.0f;
    Vec2 scale{1.0f, 1.0f};
};

class GameObject {
public:
    explicit GameObject(std::string name);
    ~GameObject();
    GameObject(const GameObject&) = delete;
    GameObject& operator=(const GameObject&) = delete;

    template <typename T, typename... Args>
    T* AddComponent(Args&&... args) {
        static_assert(std::is_base_of<Component, T>::value, "T must derive from Component");
        T* comp = new T(std::forward<Args>(args)...);
        comp->owner_ = this;
        components_.push_back(comp);
        comp->OnInit();
        return comp;
    }

    template <typename T>
    T* GetComponent() {
        static_assert(std::is_base_of<Component, T>::value, "T must derive from Component");
        for (Component* c : components_) {
            if (T* t = dynamic_cast<T*>(c)) {
                return t;
            }
        }
        return nullptr;
    }

    void Destroy();
    Component* AddComponentRaw(Component* comp) {
        comp->owner_ = this;
        components_.push_back(comp);
        comp->OnInit();
        return comp;
    }

    void RemoveComponent(Component* comp) {
        const auto it = std::find(components_.begin(), components_.end(), comp);
        if (it == components_.end()) {
            return;
        }
        (*it)->OnDestroy();
        delete *it;
        components_.erase(it);
    }

    const std::string& name() const { return name_; }
    void set_name(const std::string& name) { name_ = name; }
    bool active() const { return active_; }
    void set_active(bool active) { active_ = active; }
    bool pending_destroy() const { return pending_destroy_; }
    const std::vector<Component*>& components() const { return components_; }

    Transform transform;

private:
    friend class Scene;
    void DestroyComponents();

    std::string name_;
    std::vector<Component*> components_;
    bool active_ = true;
    bool pending_destroy_ = false;
};

}  // namespace ge
