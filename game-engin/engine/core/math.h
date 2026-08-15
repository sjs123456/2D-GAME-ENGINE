#pragma once

#include <cmath>

namespace ge {

struct Vec2 {
    float x = 0.0f;
    float y = 0.0f;

    Vec2 operator+(const Vec2& rhs) const { return {x + rhs.x, y + rhs.y}; }
    Vec2 operator-(const Vec2& rhs) const { return {x - rhs.x, y - rhs.y}; }
    Vec2 operator-() const { return {-x, -y}; }
    Vec2 operator*(float s) const { return {x * s, y * s}; }
    Vec2 operator/(float s) const { return {x / s, y / s}; }
    Vec2& operator+=(const Vec2& rhs) {
        x += rhs.x;
        y += rhs.y;
        return *this;
    }
    Vec2& operator-=(const Vec2& rhs) {
        x -= rhs.x;
        y -= rhs.y;
        return *this;
    }
};

struct Vec4 {
    float r = 0.0f;
    float g = 0.0f;
    float b = 0.0f;
    float a = 1.0f;
};

struct Rect {
    float min_x = 0.0f;
    float min_y = 0.0f;
    float max_x = 0.0f;
    float max_y = 0.0f;

    static Rect from_center(Vec2 center, Vec2 half_extents) {
        return {center.x - half_extents.x, center.y - half_extents.y,
                center.x + half_extents.x, center.y + half_extents.y};
    }

    bool intersects(const Rect& o) const {
        return min_x < o.max_x && max_x > o.min_x && min_y < o.max_y && max_y > o.min_y;
    }

    float width() const { return max_x - min_x; }
    float height() const { return max_y - min_y; }
};

struct Mat4 {    float m[16] = {0};

    static Mat4 identity() {
        Mat4 out;
        out.m[0] = 1.0f;
        out.m[5] = 1.0f;
        out.m[10] = 1.0f;
        out.m[15] = 1.0f;
        return out;
    }

    static Mat4 ortho(float left, float right, float bottom, float top, float near_z, float far_z) {
        Mat4 out = identity();
        out.m[0] = 2.0f / (right - left);
        out.m[5] = 2.0f / (top - bottom);
        out.m[10] = -2.0f / (far_z - near_z);
        out.m[12] = -(right + left) / (right - left);
        out.m[13] = -(top + bottom) / (top - bottom);
        out.m[14] = -(far_z + near_z) / (far_z - near_z);
        return out;
    }

    static Mat4 translation(float x, float y) {
        Mat4 out = identity();
        out.m[12] = x;
        out.m[13] = y;
        return out;
    }

    static Mat4 rotation_z(float radians) {
        Mat4 out = identity();
        const float c = std::cos(radians);
        const float s = std::sin(radians);
        out.m[0] = c;
        out.m[1] = s;
        out.m[4] = -s;
        out.m[5] = c;
        return out;
    }

    static Mat4 scale(float sx, float sy) {
        Mat4 out = identity();
        out.m[0] = sx;
        out.m[5] = sy;
        return out;
    }

    Mat4 mul(const Mat4& rhs) const {
        Mat4 out;
        for (int c = 0; c < 4; ++c) {
            for (int r = 0; r < 4; ++r) {
                out.m[c * 4 + r] = m[r] * rhs.m[c * 4 + 0] +
                                   m[4 + r] * rhs.m[c * 4 + 1] +
                                   m[8 + r] * rhs.m[c * 4 + 2] +
                                   m[12 + r] * rhs.m[c * 4 + 3];
            }
        }
        return out;
    }
};

}  // namespace ge
