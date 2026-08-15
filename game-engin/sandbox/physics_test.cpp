#include <cstdio>

#include "core/logger.h"
#include "ecs/gameobject.h"
#include "ecs/scene.h"
#include "physics/collider.h"
#include "physics/physics_world.h"
#include "physics/rigidbody.h"

int main() {
    ge::Logger::instance().set_min_level(ge::LogLevel::Error);

    ge::PhysicsWorld world;
    ge::Scene scene;

    ge::GameObject* floor = scene.CreateEntity("floor");
    floor->transform.pos = {0.0f, -350.0f};
    ge::RigidBody* floor_rb = floor->AddComponent<ge::RigidBody>();
    floor_rb->is_static = true;
    ge::BoxCollider* floor_col = floor->AddComponent<ge::BoxCollider>();
    floor_col->size = {1900.0f, 80.0f};

    for (int i = 0; i < 3; ++i) {
        ge::GameObject* ball = scene.CreateEntity("ball");
        ball->transform.pos = {static_cast<float>(i * 30 - 30), -200.0f};
        ge::RigidBody* rb = ball->AddComponent<ge::RigidBody>();
        rb->restitution = 0.05f;
        ge::CircleCollider* col = ball->AddComponent<ge::CircleCollider>();
        col->radius = 11.0f;
    }

    for (int step = 0; step < 300; ++step) {
        world.step(scene, 1.0f / 60.0f);
        if (step % 60 == 0) {
            ge::GameObject* b = scene.entities()[1];
            const ge::RigidBody* rb = b->GetComponent<ge::RigidBody>();
            std::printf("step %3d: ball1 y=%.1f v=(%.1f, %.1f) contacts=%zu\n",
                        step, b->transform.pos.y, rb->velocity.x, rb->velocity.y,
                        world.stats().contacts);
        }
    }

    ge::GameObject* b = scene.entities()[1];
    const ge::RigidBody* rb = b->GetComponent<ge::RigidBody>();
    std::printf("FINAL: y=%.1f v=(%.1f, %.1f) contacts=%zu enter=%zu\n",
                b->transform.pos.y, rb->velocity.x, rb->velocity.y,
                world.stats().contacts, world.stats().enter_events);
    return 0;
}
