#pragma once

#include <vector>

#include "core/math.h"
#include "render/shader.h"
#include "render/texture.h"
#include "render/texture_atlas.h"

namespace ge {

class Renderer2D;

Renderer2D& g_renderer();
void bind_renderer(Renderer2D* renderer);

struct QuadVertex {
    float x, y;
    float u, v;
    float r, g, b, a;
};

class Renderer2D {
public:
    Renderer2D() = default;
    ~Renderer2D();
    Renderer2D(const Renderer2D&) = delete;
    Renderer2D& operator=(const Renderer2D&) = delete;

    bool init(size_t max_quads = 20000);
    void shutdown();

    void begin_frame(const Mat4& view_proj);
    void draw_sprite(const Texture& texture, const UvRect& uv,
                     Vec2 pos, float rot, Vec2 scale, const Vec4& color,
                     int layer, int sort_order);
    void draw_quad(Vec2 pos, float rot, Vec2 scale, const Vec4& color,
                   int layer, int sort_order);
    void flush();
    void end_frame();

    unsigned int quad_count() const { return quad_count_; }
    unsigned int draw_calls() const { return draw_calls_; }

private:
    struct QuadDesc {
        size_t quad_index;
        int layer;
        int sort_order;
        unsigned int texture_id;
    };

    void push_quad(const QuadVertex* verts, const Texture& texture,
                   int layer, int sort_order);

    ShaderProgram shader_;
    unsigned int vao_ = 0;
    unsigned int vbo_ = 0;
    Texture white_texture_;
    size_t max_quads_ = 0;
    std::vector<QuadVertex> vertices_;
    std::vector<QuadVertex> sorted_vertices_;
    std::vector<QuadDesc> descriptors_;
    Mat4 view_proj_;
    bool in_frame_ = false;
    unsigned int quad_count_ = 0;
    unsigned int draw_calls_ = 0;
};

}  // namespace ge