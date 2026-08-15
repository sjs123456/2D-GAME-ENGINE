#include "render/renderer2d.h"

#include <algorithm>
#include <cmath>

#include <glad/glad.h>

#include "core/logger.h"

namespace ge {

namespace {

const char* kVertexSrc =
    "#version 330 core\n"
    "layout(location = 0) in vec2 aPos;\n"
    "layout(location = 1) in vec2 aUV;\n"
    "layout(location = 2) in vec4 aColor;\n"
    "uniform mat4 uViewProj;\n"
    "out vec2 vUV;\n"
    "out vec4 vColor;\n"
    "void main() {\n"
    "    vUV = aUV;\n"
    "    vColor = aColor;\n"
    "    gl_Position = uViewProj * vec4(aPos, 0.0, 1.0);\n"
    "}\n";

const char* kFragmentSrc =
    "#version 330 core\n"
    "in vec2 vUV;\n"
    "in vec4 vColor;\n"
    "uniform sampler2D uTex;\n"
    "out vec4 fragColor;\n"
    "void main() { fragColor = texture(uTex, vUV) * vColor; }\n";

void build_quad_vertices(QuadVertex* out, Vec2 pos, float rot, Vec2 scale,
                         const UvRect& uv, const Vec4& color) {
    const float c = std::cos(rot);
    const float s = std::sin(rot);
    const float hx = scale.x * 0.5f;
    const float hy = scale.y * 0.5f;
    const float corners[4][2] = {
        {-hx, -hy}, {hx, -hy}, {hx, hy}, {-hx, hy},
    };
    const float uvs[4][2] = {
        {uv.u0, uv.v0}, {uv.u1, uv.v0}, {uv.u1, uv.v1}, {uv.u0, uv.v1},
    };
    const int order[6] = {0, 1, 2, 0, 2, 3};
    for (int i = 0; i < 6; ++i) {
        const int idx = order[i];
        const float lx = corners[idx][0];
        const float ly = corners[idx][1];
        QuadVertex& v = out[i];
        v.x = c * lx - s * ly + pos.x;
        v.y = s * lx + c * ly + pos.y;
        v.u = uvs[idx][0];
        v.v = uvs[idx][1];
        v.r = color.r;
        v.g = color.g;
        v.b = color.b;
        v.a = color.a;
    }
}

}  // namespace

namespace {
Renderer2D* s_renderer = nullptr;
}

Renderer2D& g_renderer() {
    static Renderer2D fallback;
    return s_renderer ? *s_renderer : fallback;
}

void bind_renderer(Renderer2D* renderer) {
    s_renderer = renderer;
}

Renderer2D::~Renderer2D() {
    if (s_renderer == this) {
        s_renderer = nullptr;
    }
    shutdown();
}

bool Renderer2D::init(size_t max_quads) {
    max_quads_ = max_quads;
    vertices_.reserve(max_quads_ * 6);
    sorted_vertices_.resize(max_quads_ * 6);
    descriptors_.reserve(max_quads_);

    if (!shader_.compile(kVertexSrc, kFragmentSrc)) {
        GE_LOG_ERROR("Renderer2D shader compile failed");
        return false;
    }

    const unsigned char white[4] = {255, 255, 255, 255};
    if (!white_texture_.create_from_pixels(1, 1, white)) {
        GE_LOG_ERROR("Renderer2D white texture creation failed");
        return false;
    }

    glGenVertexArrays(1, &vao_);
    glGenBuffers(1, &vbo_);
    glBindVertexArray(vao_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER,
                 static_cast<GLsizeiptr>(max_quads_ * 6 * sizeof(QuadVertex)),
                 nullptr, GL_DYNAMIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, sizeof(QuadVertex), (void*)offsetof(QuadVertex, x));
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, sizeof(QuadVertex), (void*)offsetof(QuadVertex, u));
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, sizeof(QuadVertex), (void*)offsetof(QuadVertex, r));
    glBindVertexArray(0);

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    return true;
}

void Renderer2D::shutdown() {
    if (vao_) {
        glDeleteVertexArrays(1, &vao_);
        vao_ = 0;
    }
    if (vbo_) {
        glDeleteBuffers(1, &vbo_);
        vbo_ = 0;
    }
    white_texture_.destroy();
    vertices_.clear();
    descriptors_.clear();
}

void Renderer2D::begin_frame(const Mat4& view_proj) {
    view_proj_ = view_proj;
    vertices_.clear();
    descriptors_.clear();
    quad_count_ = 0;
    draw_calls_ = 0;
    in_frame_ = true;
}

void Renderer2D::draw_sprite(const Texture& texture, const UvRect& uv,
                             Vec2 pos, float rot, Vec2 scale, const Vec4& color,
                             int layer, int sort_order) {
    if (!in_frame_) {
        return;
    }
    if (quad_count_ >= max_quads_) {
        GE_LOG_WARN("Renderer2D quad buffer full (%u)", static_cast<unsigned int>(max_quads_));
        return;
    }
    QuadVertex verts[6];
    build_quad_vertices(verts, pos, rot, scale, uv, color);
    push_quad(verts, texture, layer, sort_order);
}

void Renderer2D::draw_quad(Vec2 pos, float rot, Vec2 scale, const Vec4& color,
                           int layer, int sort_order) {
    static const UvRect kFullUv{0.0f, 0.0f, 1.0f, 1.0f};
    draw_sprite(white_texture_, kFullUv, pos, rot, scale, color, layer, sort_order);
}

void Renderer2D::push_quad(const QuadVertex* verts, const Texture& texture,
                           int layer, int sort_order) {
    const size_t quad_index = quad_count_++;
    vertices_.insert(vertices_.end(), verts, verts + 6);
    descriptors_.push_back(QuadDesc{quad_index, layer, sort_order, texture.handle()});
}

void Renderer2D::flush() {
    if (!in_frame_ || vertices_.empty()) {
        return;
    }

    std::sort(descriptors_.begin(), descriptors_.end(),
              [](const QuadDesc& a, const QuadDesc& b) {
                  if (a.layer != b.layer) return a.layer < b.layer;
                  if (a.sort_order != b.sort_order) return a.sort_order < b.sort_order;
                  return a.texture_id < b.texture_id;
              });

    for (const QuadDesc& d : descriptors_) {
        std::copy(vertices_.begin() + static_cast<long>(d.quad_index * 6),
                  vertices_.begin() + static_cast<long>(d.quad_index * 6) + 6,
                  sorted_vertices_.begin() + static_cast<long>(d.quad_index * 6));
    }

    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER,
                 static_cast<GLsizeiptr>(vertices_.size() * sizeof(QuadVertex)),
                 sorted_vertices_.data(), GL_DYNAMIC_DRAW);

    glBindVertexArray(vao_);
    shader_.use();
    shader_.set_mat4("uViewProj", view_proj_.m);

    size_t i = 0;
    while (i < descriptors_.size()) {
        const unsigned int texture_id = descriptors_[i].texture_id;
        size_t j = i;
        while (j < descriptors_.size() && descriptors_[j].texture_id == texture_id) {
            ++j;
        }
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, texture_id);
        glDrawArrays(GL_TRIANGLES,
                     static_cast<GLint>(i * 6),
                     static_cast<GLsizei>((j - i) * 6));
        ++draw_calls_;
        i = j;
    }
}

void Renderer2D::end_frame() {
    flush();
    glBindVertexArray(0);
    glBindTexture(GL_TEXTURE_2D, 0);
    in_frame_ = false;
}

}  // namespace ge
