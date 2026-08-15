#include "physics/physics_world.h"

#include <algorithm>
#include <cmath>

#include "ecs/component.h"
#include "physics/collider.h"
#include "physics/rigidbody.h"

namespace ge {

namespace {
constexpr float kEps = 1e-5f;

int64_t cell_key(int cx, int cy) {
    return (static_cast<int64_t>(static_cast<uint32_t>(cx)) << 32) |
           static_cast<uint32_t>(cy);
}

bool circle_circle(Vec2 c1, float r1, Vec2 c2, float r2, float slop, Vec2& normal, float& penetration) {
    const Vec2 delta = c2 - c1;
    const float dist2 = delta.x * delta.x + delta.y * delta.y;
    const float rsum = r1 + r2;
    if (dist2 > (rsum + slop) * (rsum + slop)) {
        return false;
    }
    if (dist2 < kEps) {
        normal = {0.0f, 1.0f};
        penetration = rsum;
        return true;
    }
    const float dist = std::sqrt(dist2);
    normal = delta / dist;
    penetration = rsum - dist;
    return true;
}

bool box_box(const Rect& a, const Rect& b, Vec2 ca, Vec2 cb, Vec2 prev_ca, Vec2 prev_cb,
             float slop, bool a_one_way, bool b_one_way, Vec2& normal, float& penetration) {
    const float ox = std::min(a.max_x, b.max_x) - std::max(a.min_x, b.min_x);
    const float oy = std::min(a.max_y, b.max_y) - std::max(a.min_y, b.min_y);
    if (a_one_way && !b_one_way) {
        if (prev_cb.y <= a.max_y - 1.0f) {
            return false;
        }
        if (oy <= -slop || ox <= -slop) {
            return false;
        }
        normal = {0.0f, 1.0f};
        penetration = oy;
        return true;
    }
    if (b_one_way && !a_one_way) {
        if (prev_ca.y <= b.max_y - 1.0f) {
            return false;
        }
        if (oy <= -slop || ox <= -slop) {
            return false;
        }
        normal = {0.0f, 1.0f};
        penetration = oy;
        return true;
    }
    if (ox <= -slop || oy <= -slop) {
        return false;
    }
    if (ox < oy) {
        normal = {cb.x >= ca.x ? 1.0f : -1.0f, 0.0f};
        penetration = ox;
    } else {
        normal = {0.0f, cb.y >= ca.y ? 1.0f : -1.0f};
        penetration = oy;
    }
    return true;
}

bool circle_box(Vec2 cc, float r, const Rect& box, Vec2 prev_cc, float slop,
                Vec2& normal, float& penetration) {
    const float closest_x = std::clamp(cc.x, box.min_x, box.max_x);
    const float closest_y = std::clamp(cc.y, box.min_y, box.max_y);
    const Vec2 delta = cc - Vec2{closest_x, closest_y};
    const float dist2 = delta.x * delta.x + delta.y * delta.y;
    if (dist2 > (r + slop) * (r + slop) && dist2 > kEps) {
        return false;
    }
    if (dist2 < kEps) {
        Vec2 entry{0.0f, 1.0f};
        if (prev_cc.y > box.max_y) {
            entry = {0.0f, 1.0f};
        } else if (prev_cc.y < box.min_y) {
            entry = {0.0f, -1.0f};
        } else if (prev_cc.x < box.min_x) {
            entry = {-1.0f, 0.0f};
        } else if (prev_cc.x > box.max_x) {
            entry = {1.0f, 0.0f};
        }
        const float box_cx = (box.min_x + box.max_x) * 0.5f;
        const float box_cy = (box.min_y + box.max_y) * 0.5f;
        const float overlap_x = std::min(cc.x - box.min_x, box.max_x - cc.x);
        const float overlap_y = std::min(cc.y - box.min_y, box.max_y - cc.y);
        if (overlap_x < overlap_y) {
            normal = {cc.x < box_cx ? -1.0f : 1.0f, 0.0f};
            penetration = overlap_x + r;
        } else {
            normal = {0.0f, cc.y < box_cy ? -1.0f : 1.0f};
            penetration = overlap_y + r;
        }
        if (normal.x * entry.x + normal.y * entry.y < 0.0f) {
            normal = entry;
        }
        return true;
    }
    const float dist = std::sqrt(dist2);
    normal = delta / dist;
    penetration = r - dist;
    return true;
}

}  // namespace

void PhysicsWorld::compute_aabb(Body& b) {
    Vec2 center = b.object->transform.pos;
    if (b.circle) {
        center += b.circle->offset;
        b.aabb = Rect::from_center(center, {b.circle->radius, b.circle->radius});
    } else if (b.box) {
        center += b.box->offset;
        b.aabb = Rect::from_center(center, {b.box->size.x * 0.5f, b.box->size.y * 0.5f});
    }
}

bool PhysicsWorld::narrow(const Body& a, const Body& b, Vec2& normal, float& penetration) const {
    Vec2 ca = a.object->transform.pos;
    Vec2 cb = b.object->transform.pos;
    Vec2 prev_ca = a.rb ? a.rb->prev_pos : ca;
    Vec2 prev_cb = b.rb ? b.rb->prev_pos : cb;
    if (a.circle) {
        ca += a.circle->offset;
        prev_ca += a.circle->offset;
    }
    if (b.circle) {
        cb += b.circle->offset;
        prev_cb += b.circle->offset;
    }

    if (a.circle && b.circle) {
        if (!circle_circle(ca, a.circle->radius, cb, b.circle->radius,
                           settings_.slop, normal, penetration)) {
            return false;
        }
    } else if (a.box && b.box) {
        const bool a_one_way = a.box->one_way;
        const bool b_one_way = b.box->one_way;
        if (!box_box(a.aabb, b.aabb, ca, cb, prev_ca, prev_cb,
                     settings_.slop, a_one_way, b_one_way, normal, penetration)) {
            return false;
        }
    } else if (a.circle && b.box) {
        if (!circle_box(ca, a.circle->radius, b.aabb, prev_ca,
                        settings_.slop, normal, penetration)) {
            return false;
        }
        normal = -normal;
    } else if (a.box && b.circle) {
        if (!circle_box(cb, b.circle->radius, a.aabb, prev_cb,
                        settings_.slop, normal, penetration)) {
            return false;
        }
    } else {
        return false;
    }
    return penetration > -settings_.slop;
}

void PhysicsWorld::solve_position(Body& a, Body& b, const Vec2& normal, float penetration) {
    const bool a_dyn = !a.is_static;
    const bool b_dyn = !b.is_static;
    if (!a_dyn && !b_dyn) {
        return;
    }
    const float inv_a = a_dyn ? 1.0f / a.mass : 0.0f;
    const float inv_b = b_dyn ? 1.0f / b.mass : 0.0f;
    const float inv_sum = inv_a + inv_b;
    if (inv_sum <= kEps) {
        return;
    }
    if (a.box && a.box->one_way) {
        if (b_dyn) {
            b.object->transform.pos.y += penetration * inv_b / inv_sum;
        }
        return;
    }
    if (b.box && b.box->one_way) {
        if (a_dyn) {
            a.object->transform.pos.y += penetration * inv_a / inv_sum;
        }
        return;
    }
    if (a_dyn) {
        a.object->transform.pos -= normal * (penetration * inv_a / inv_sum);
    }
    if (b_dyn) {
        b.object->transform.pos += normal * (penetration * inv_b / inv_sum);
    }
}

void PhysicsWorld::dispatch_events() {
    std::vector<std::pair<uintptr_t, uintptr_t>> curr_pairs;
    curr_pairs.reserve(contacts_.size());
    for (const Contact& c : contacts_) {
        const uintptr_t ap = reinterpret_cast<uintptr_t>(c.a->object);
        const uintptr_t bp = reinterpret_cast<uintptr_t>(c.b->object);
        curr_pairs.push_back({std::min(ap, bp), std::max(ap, bp)});
    }
    std::sort(curr_pairs.begin(), curr_pairs.end());
    curr_pairs.erase(std::unique(curr_pairs.begin(), curr_pairs.end()), curr_pairs.end());

    auto key_of = [](const Contact& c) {
        const uintptr_t ap = reinterpret_cast<uintptr_t>(c.a->object);
        const uintptr_t bp = reinterpret_cast<uintptr_t>(c.b->object);
        return std::make_pair(std::min(ap, bp), std::max(ap, bp));
    };
    std::sort(contacts_.begin(), contacts_.end(),
              [&](const Contact& x, const Contact& y) { return key_of(x) < key_of(y); });

    size_t pi = 0;
    size_t ci = 0;
    while (pi < prev_pairs_.size() || ci < contacts_.size()) {
        if (ci >= contacts_.size()) {
            auto* ga = reinterpret_cast<GameObject*>(prev_pairs_[pi].first);
            auto* gb = reinterpret_cast<GameObject*>(prev_pairs_[pi].second);
            for (Component* comp : ga->components()) {
                comp->OnCollisionExit(CollisionInfo{gb, {0.0f, 0.0f}, 0.0f});
            }
            for (Component* comp : gb->components()) {
                comp->OnCollisionExit(CollisionInfo{ga, {0.0f, 0.0f}, 0.0f});
            }
            ++stats_.exit_events;
            ++pi;
        } else if (pi >= prev_pairs_.size()) {
            const Contact& c = contacts_[ci];
            for (Component* comp : c.a->object->components()) {
                comp->OnCollisionEnter(CollisionInfo{c.b->object, -c.normal, c.penetration, c.impact_speed});
            }
            for (Component* comp : c.b->object->components()) {
                comp->OnCollisionEnter(CollisionInfo{c.a->object, c.normal, c.penetration, c.impact_speed});
            }
            ++stats_.enter_events;
            ++ci;
        } else if (prev_pairs_[pi] == key_of(contacts_[ci])) {
            const Contact& c = contacts_[ci];
            for (Component* comp : c.a->object->components()) {
                comp->OnCollisionStay(CollisionInfo{c.b->object, -c.normal, c.penetration, c.impact_speed});
            }
            for (Component* comp : c.b->object->components()) {
                comp->OnCollisionStay(CollisionInfo{c.a->object, c.normal, c.penetration, c.impact_speed});
            }
            ++pi;
            ++ci;
        } else if (prev_pairs_[pi] < key_of(contacts_[ci])) {
            auto* ga = reinterpret_cast<GameObject*>(prev_pairs_[pi].first);
            auto* gb = reinterpret_cast<GameObject*>(prev_pairs_[pi].second);
            for (Component* comp : ga->components()) {
                comp->OnCollisionExit(CollisionInfo{gb, {0.0f, 0.0f}, 0.0f});
            }
            for (Component* comp : gb->components()) {
                comp->OnCollisionExit(CollisionInfo{ga, {0.0f, 0.0f}, 0.0f});
            }
            ++stats_.exit_events;
            ++pi;
        } else {
            const Contact& c = contacts_[ci];
            for (Component* comp : c.a->object->components()) {
                comp->OnCollisionEnter(CollisionInfo{c.b->object, -c.normal, c.penetration, c.impact_speed});
            }
            for (Component* comp : c.b->object->components()) {
                comp->OnCollisionEnter(CollisionInfo{c.a->object, c.normal, c.penetration, c.impact_speed});
            }
            ++stats_.enter_events;
            ++ci;
        }
    }

    prev_pairs_ = std::move(curr_pairs);
}

void PhysicsWorld::step(Scene& scene, float dt) {
    if (scene.generation() != scene_generation_) {
        prev_pairs_.clear();
        scene_generation_ = scene.generation();
    }
    bodies_.clear();
    for (GameObject* go : scene.entities()) {
        if (!go->active() || go->pending_destroy()) {
            continue;
        }
        Body b;
        b.object = go;
        b.rb = go->GetComponent<RigidBody>();
        b.circle = go->GetComponent<CircleCollider>();
        b.box = go->GetComponent<BoxCollider>();
        if (!b.rb && !b.circle && !b.box) {
            continue;
        }
        if (b.rb) {
            b.velocity = b.rb->velocity;
            b.restitution = b.rb->restitution;
            b.mass = b.rb->mass;
            b.is_static = b.rb->is_static;
        }
        if (b.is_static) {
            b.velocity = {0.0f, 0.0f};
            b.restitution = 0.0f;
        }
        compute_aabb(b);
        bodies_.push_back(b);
    }

    for (Body& b : bodies_) {
        if (b.is_static) {
            continue;
        }
        b.rb->prev_pos = b.object->transform.pos;
        if (b.rb->at_rest) {
            b.velocity = {0.0f, 0.0f};
            continue;
        }
        b.velocity += settings_.gravity * (b.rb->gravity_scale * dt);
        const float speed_sq = b.velocity.x * b.velocity.x + b.velocity.y * b.velocity.y;
        if (speed_sq > settings_.max_speed * settings_.max_speed) {
            const float scale = settings_.max_speed / std::sqrt(speed_sq);
            b.velocity = b.velocity * scale;
        }
        b.object->transform.pos += b.velocity * dt;
        compute_aabb(b);
    }

    grid_.clear();
    for (int i = 0; i < static_cast<int>(bodies_.size()); ++i) {
        const Rect& aabb = bodies_[i].aabb;
        const int cx0 = static_cast<int>(std::floor(aabb.min_x / settings_.cell_size));
        const int cx1 = static_cast<int>(std::floor(aabb.max_x / settings_.cell_size));
        const int cy0 = static_cast<int>(std::floor(aabb.min_y / settings_.cell_size));
        const int cy1 = static_cast<int>(std::floor(aabb.max_y / settings_.cell_size));
        for (int cy = cy0; cy <= cy1; ++cy) {
            for (int cx = cx0; cx <= cx1; ++cx) {
                grid_[cell_key(cx, cy)].push_back(i);
            }
        }
    }

    pairs_.clear();
    std::vector<std::pair<int, int>> raw_pairs;
    for (int i = 0; i < static_cast<int>(bodies_.size()); ++i) {
        const Rect& aabb = bodies_[i].aabb;
        const int cx0 = static_cast<int>(std::floor(aabb.min_x / settings_.cell_size));
        const int cx1 = static_cast<int>(std::floor(aabb.max_x / settings_.cell_size));
        const int cy0 = static_cast<int>(std::floor(aabb.min_y / settings_.cell_size));
        const int cy1 = static_cast<int>(std::floor(aabb.max_y / settings_.cell_size));
        for (int cy = cy0; cy <= cy1; ++cy) {
            for (int cx = cx0; cx <= cx1; ++cx) {
                const auto it = grid_.find(cell_key(cx, cy));
                if (it == grid_.end()) {
                    continue;
                }
                for (const int j : it->second) {
                    if (j > i) {
                        raw_pairs.push_back({i, j});
                    }
                }
            }
        }
    }
    std::sort(raw_pairs.begin(), raw_pairs.end());
    raw_pairs.erase(std::unique(raw_pairs.begin(), raw_pairs.end()), raw_pairs.end());
    pairs_ = std::move(raw_pairs);

    contacts_.clear();
    has_contact_.assign(bodies_.size(), false);

    for (int iter = 0; iter < settings_.iterations; ++iter) {
        for (const auto& [ia, ib] : pairs_) {
            Body& a = bodies_[ia];
            Body& b = bodies_[ib];
            Vec2 normal{0.0f, 0.0f};
            float penetration = 0.0f;
            const bool hit = narrow(a, b, normal, penetration);
            if (hit) {
                if (penetration > settings_.slop) {
                    solve_position(a, b, normal, penetration);
                }
                has_contact_[ia] = true;
                has_contact_[ib] = true;
                if (iter == settings_.iterations - 1) {
                    contacts_.push_back(Contact{&bodies_[ia], &bodies_[ib], normal, penetration});
                }
            }
        }
        for (Body& body : bodies_) {
            if (!body.is_static) {
                compute_aabb(body);
            }
        }
    }

    auto clamp_speed = [this](Body& b) {
        if (b.is_static) {
            return;
        }
        const float speed_sq = b.velocity.x * b.velocity.x + b.velocity.y * b.velocity.y;
        if (speed_sq > settings_.max_speed * settings_.max_speed) {
            const float scale = settings_.max_speed / std::sqrt(speed_sq);
            b.velocity = b.velocity * scale;
        }
    };

    for (int viter = 0; viter < settings_.velocity_iterations; ++viter) {
        for (Contact& c : contacts_) {
            const float restitution = std::max(c.a->restitution, c.b->restitution);
            const float inv_a = c.a->is_static ? 0.0f : 1.0f / c.a->mass;
            const float inv_b = c.b->is_static ? 0.0f : 1.0f / c.b->mass;
            const float inv_sum = inv_a + inv_b;
            if (inv_sum <= kEps) {
                continue;
            }
            const Vec2 rel = c.b->velocity - c.a->velocity;
            const float vn = rel.x * c.normal.x + rel.y * c.normal.y;
            if (vn < 0.0f) {
                c.impact_speed = -vn;
                const bool bouncing = vn < -settings_.bounce_min_speed;
                const float e = bouncing ? restitution : 0.0f;
                const float j = -(1.0f + e) * vn / inv_sum;
                if (!c.a->is_static) {
                    c.a->velocity -= c.normal * (j * inv_a);
                }
                if (!c.b->is_static) {
                    c.b->velocity += c.normal * (j * inv_b);
                }

                const Vec2 tangent{-c.normal.y, c.normal.x};
                const float vt = rel.x * tangent.x + rel.y * tangent.y;
                const float friction = bouncing ? 0.2f : 1.0f;
                const float jt = -vt * friction / inv_sum;
                if (!c.a->is_static) {
                    c.a->velocity -= tangent * (jt * inv_a);
                }
                if (!c.b->is_static) {
                    c.b->velocity += tangent * (jt * inv_b);
                }
            }
        }
        for (Body& b : bodies_) {
            clamp_speed(b);
        }
    }

    for (int i = 0; i < static_cast<int>(bodies_.size()); ++i) {
        Body& b = bodies_[i];
        if (b.is_static) {
            continue;
        }
        b.rb->velocity = b.velocity;
        if (b.velocity.x != 0.0f || b.velocity.y != 0.0f) {
            b.rb->at_rest = false;
        }
        if (has_contact_[i]) {
            const float speed_sq = b.velocity.x * b.velocity.x + b.velocity.y * b.velocity.y;
            if (speed_sq < settings_.resting_speed * settings_.resting_speed) {
                b.rb->velocity = {0.0f, 0.0f};
                b.rb->at_rest = true;
            }
        }
    }

    stats_.bodies = bodies_.size();
    stats_.pairs = pairs_.size();
    stats_.contacts = contacts_.size();
    dispatch_events();
}

}  // namespace ge
