#pragma once

#include <cstdint>
#include <unordered_map>
#include <utility>
#include <vector>

#include "core/math.h"
#include "ecs/scene.h"

namespace ge {

class RigidBody;
class CircleCollider;
class BoxCollider;

class PhysicsWorld {
public:
    struct Settings {
        Vec2 gravity{0.0f, -1500.0f};
        int iterations = 10;
        float cell_size = 32.0f;
        float max_speed = 2500.0f;
        float resting_speed = 60.0f;
        float bounce_min_speed = 60.0f;
        float slop = 2.0f;
        int velocity_iterations = 8;
    };

    struct Stats {
        size_t bodies = 0;
        size_t pairs = 0;
        size_t contacts = 0;
        size_t enter_events = 0;
        size_t exit_events = 0;
    };

    explicit PhysicsWorld(Settings settings) : settings_(std::move(settings)) {}
    PhysicsWorld() : settings_() {}

    void step(Scene& scene, float dt);
    const Stats& stats() const { return stats_; }    void reset_event_counts() {
        stats_.enter_events = 0;
        stats_.exit_events = 0;
    }

private:
    struct Body {
        GameObject* object = nullptr;
        RigidBody* rb = nullptr;
        CircleCollider* circle = nullptr;
        BoxCollider* box = nullptr;
        Vec2 velocity{0.0f, 0.0f};
        float restitution = 0.0f;
        float mass = 1.0f;
        bool is_static = false;
        Rect aabb;
    };

    struct Contact {
        Body* a = nullptr;
        Body* b = nullptr;
        Vec2 normal{0.0f, 0.0f};
        float penetration = 0.0f;
        float impact_speed = 0.0f;
    };

    void compute_aabb(Body& b);
    bool narrow(const Body& a, const Body& b, Vec2& normal, float& penetration) const;
    void solve_position(Body& a, Body& b, const Vec2& normal, float penetration);
    void dispatch_events();

    Settings settings_;
    std::vector<Body> bodies_;
    std::vector<bool> has_contact_;
    std::unordered_map<int64_t, std::vector<int>> grid_;
    std::vector<std::pair<int, int>> pairs_;
    std::vector<Contact> contacts_;
    std::vector<std::pair<uintptr_t, uintptr_t>> prev_pairs_;
    unsigned int scene_generation_ = 0;
    Stats stats_;
};

}  // namespace ge
