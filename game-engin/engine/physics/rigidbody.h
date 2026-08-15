#pragma once

#include "core/math.h"
#include "ecs/component.h"

namespace ge {

class RigidBody : public Component {
public:
    Vec2 velocity{0.0f, 0.0f};
    Vec2 prev_pos{0.0f, 0.0f};
    float gravity_scale = 1.0f;
    float restitution = 0.2f;
    float mass = 1.0f;
    bool is_static = false;
    bool at_rest = false;
};

}  // namespace ge
