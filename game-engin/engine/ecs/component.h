#pragma once

#include "core/math.h"

namespace ge {

class GameObject;

struct CollisionInfo {
    GameObject* other = nullptr;
    Vec2 normal{0.0f, 0.0f};
    float penetration = 0.0f;
    float impact_speed = 0.0f;
};

class Component {
public:
    virtual ~Component() = default;

    GameObject* owner() const { return owner_; }
    bool is_active() const { return active_; }
    void set_active(bool active) { active_ = active; }

    virtual void OnInit() {}
    virtual void OnUpdate(float) {}
    virtual void OnRender(float) {}
    virtual void OnCollisionEnter(const CollisionInfo&) {}
    virtual void OnCollisionStay(const CollisionInfo&) {}
    virtual void OnCollisionExit(const CollisionInfo&) {}
    virtual void OnDestroy() {}

private:
    friend class GameObject;
    GameObject* owner_ = nullptr;
    bool active_ = true;
};

}  // namespace ge
