#pragma once

#include "core/math.h"
#include "ecs/component.h"
#include "physics/rigidbody.h"
#include "render/renderer2d.h"
#include "render/texture_atlas.h"

namespace ge {

class SpriteRenderer : public Component {
public:
    Texture* texture = nullptr;
    UvRect uv{0.0f, 0.0f, 1.0f, 1.0f};
    Vec4 color{1.0f, 1.0f, 1.0f, 1.0f};
    int layer = 100;
    int sort_order = 0;
    bool interpolate = true;

    void set_frame(TextureAtlas* atlas, const char* frame_name) {
        texture = atlas->texture();
        if (const UvRect* f = atlas->frame(frame_name)) {
            uv = *f;
        }
    }

    void OnRender(float alpha) override {
        if (!texture) {
            return;
        }
        const Transform& t = owner()->transform;
        Vec2 render_pos = t.pos;
        if (interpolate) {
            if (const RigidBody* rb = owner()->GetComponent<RigidBody>()) {
                render_pos = rb->prev_pos + (t.pos - rb->prev_pos) * alpha;
            }
        }
        g_renderer().draw_sprite(*texture, uv, render_pos, t.rot, t.scale, color, layer, sort_order);
    }
};

}  // namespace ge
