#pragma once

#include "core/math.h"

namespace ge {

class Camera2D {
public:
    void set_position(Vec2 pos) { pos_ = pos; }
    Vec2 position() const { return pos_; }

    void set_zoom(float zoom) { zoom_ = zoom > 0.001f ? zoom : 0.001f; }
    float zoom() const { return zoom_; }

    Mat4 view_proj(float viewport_width, float viewport_height) const {
        const float half_w = (viewport_width * 0.5f) / zoom_;
        const float half_h = (viewport_height * 0.5f) / zoom_;
        const Mat4 proj = Mat4::ortho(-half_w, half_w, -half_h, half_h, -1.0f, 1.0f);
        const Mat4 view = Mat4::translation(-pos_.x, -pos_.y);
        return proj.mul(view);
    }

    Vec2 screen_to_world(Vec2 screen, float viewport_width, float viewport_height) const {
        return {
            pos_.x + (screen.x - viewport_width * 0.5f) / zoom_,
            pos_.y + (screen.y - viewport_height * 0.5f) / zoom_,
        };
    }

private:
    Vec2 pos_{0.0f, 0.0f};
    float zoom_ = 1.0f;
};

}  // namespace ge
