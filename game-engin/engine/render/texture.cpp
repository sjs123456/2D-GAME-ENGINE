#include "render/texture.h"

#include <glad/glad.h>
#include <stb_image.h>

#include "core/logger.h"

namespace ge {

namespace {
bool upload_pixels(int width, int height, const void* rgba, unsigned int& handle) {
    glGenTextures(1, &handle);
    glBindTexture(GL_TEXTURE_2D, handle);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, rgba);
    glBindTexture(GL_TEXTURE_2D, 0);
    return true;
}
}  // namespace

Texture::~Texture() {
    destroy();
}

bool Texture::load(const std::string& path) {
    stbi_set_flip_vertically_on_load(1);
    int w = 0;
    int h = 0;
    int channels = 0;
    unsigned char* data = stbi_load(path.c_str(), &w, &h, &channels, 4);
    if (!data) {
        GE_LOG_ERROR("Failed to load texture '%s': %s", path.c_str(), stbi_failure_reason());
        return false;
    }

    const bool ok = create_from_pixels(w, h, data);
    stbi_image_free(data);
    if (!ok) {
        GE_LOG_ERROR("Failed to upload texture '%s'", path.c_str());
    }
    GE_LOG_INFO("Texture loaded: %s (%dx%d)", path.c_str(), w, h);
    return ok;
}

bool Texture::create_from_pixels(int width, int height, const unsigned char* rgba) {
    if (handle_) {
        destroy();
    }
    upload_pixels(width, height, rgba, handle_);
    width_ = width;
    height_ = height;
    return handle_ != 0;
}

void Texture::destroy() {
    if (handle_) {
        glDeleteTextures(1, &handle_);
        handle_ = 0;
    }
    width_ = 0;
    height_ = 0;
}

void Texture::bind(unsigned int slot) const {
    glActiveTexture(GL_TEXTURE0 + slot);
    glBindTexture(GL_TEXTURE_2D, handle_);
}

}  // namespace ge
