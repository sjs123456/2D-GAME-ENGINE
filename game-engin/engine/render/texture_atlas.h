#pragma once

#include <string>
#include <unordered_map>

#include "core/math.h"
#include "render/texture.h"

namespace ge {

struct UvRect {
    float u0 = 0.0f;
    float v0 = 0.0f;
    float u1 = 1.0f;
    float v1 = 1.0f;
};

class TextureAtlas {
public:
    explicit TextureAtlas(Texture* texture) : texture_(texture) {}

    void add_frame(const std::string& name, const UvRect& uv) {
        frames_[name] = uv;
    }

    void add_frame_pixels(const std::string& name, int x, int y, int w, int h) {
        const float tex_w = static_cast<float>(texture_->width());
        const float tex_h = static_cast<float>(texture_->height());
        UvRect uv;
        uv.u0 = x / tex_w;
        uv.v0 = 1.0f - (y + h) / tex_h;
        uv.u1 = (x + w) / tex_w;
        uv.v1 = 1.0f - y / tex_h;
        add_frame(name, uv);
    }

    const UvRect* frame(const std::string& name) const {
        const auto it = frames_.find(name);
        return it == frames_.end() ? nullptr : &it->second;
    }

    Texture* texture() const { return texture_; }

private:
    Texture* texture_ = nullptr;
    std::unordered_map<std::string, UvRect> frames_;
};

}  // namespace ge
