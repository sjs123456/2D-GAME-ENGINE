#pragma once

#include <string>

namespace ge {

class Texture {
public:
    Texture() = default;
    ~Texture();
    Texture(const Texture&) = delete;
    Texture& operator=(const Texture&) = delete;

    bool load(const std::string& path);
    bool create_from_pixels(int width, int height, const unsigned char* rgba);
    void destroy();

    void bind(unsigned int slot = 0) const;

    unsigned int handle() const { return handle_; }
    int width() const { return width_; }
    int height() const { return height_; }
    bool valid() const { return handle_ != 0; }

private:
    unsigned int handle_ = 0;
    int width_ = 0;
    int height_ = 0;
};

}  // namespace ge
