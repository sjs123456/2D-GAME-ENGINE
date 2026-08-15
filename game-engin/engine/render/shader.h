#pragma once

namespace ge {

class ShaderProgram {
public:
    ShaderProgram() = default;
    ~ShaderProgram();
    ShaderProgram(const ShaderProgram&) = delete;
    ShaderProgram& operator=(const ShaderProgram&) = delete;

    bool compile(const char* vertex_src, const char* fragment_src);
    void use() const;
    void set_mat4(const char* name, const float* value);
    void set_vec4(const char* name, const float* value);

    bool valid() const { return valid_; }
    unsigned int handle() const { return handle_; }

private:
    unsigned int handle_ = 0;
    bool valid_ = false;
};

}  // namespace ge
