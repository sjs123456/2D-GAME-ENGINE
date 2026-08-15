#pragma once

#include "core/math.h"
#include "ecs/component.h"

namespace ge {

class CircleCollider : public Component {
public:
    float radius = 10.0f;
    Vec2 offset{0.0f, 0.0f};
};

class BoxCollider : public Component {
public:
    Vec2 size{32.0f, 32.0f};
    Vec2 offset{0.0f, 0.0f};
    bool one_way = false;
};

}  // namespace ge
