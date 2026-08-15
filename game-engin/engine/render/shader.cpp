#include "render/shader.h"

#include <glad/glad.h>

#include "core/logger.h"

namespace ge {

namespace {

unsigned int compile_shader(unsigned int type, const char* source) {
    const unsigned int id = glCreateShader(type);
    glShaderSource(id, 1, &source, nullptr);
    glCompileShader(id);

    int success = 0;
    glGetShaderiv(id, GL_COMPILE_STATUS, &success);
    if (!success) {
        char log[1024];
        glGetShaderInfoLog(id, sizeof(log), nullptr, log);
        GE_LOG_ERROR("Shader compile error (%s): %s",
                     type == GL_VERTEX_SHADER ? "vertex" : "fragment", log);
        glDeleteShader(id);
        return 0;
    }
    return id;
}

}  // namespace

ShaderProgram::~ShaderProgram() {
    if (handle_) {
        glDeleteProgram(handle_);
    }
}

bool ShaderProgram::compile(const char* vertex_src, const char* fragment_src) {
    const unsigned int vs = compile_shader(GL_VERTEX_SHADER, vertex_src);
    const unsigned int fs = compile_shader(GL_FRAGMENT_SHADER, fragment_src);
    if (!vs || !fs) {
        return false;
    }

    handle_ = glCreateProgram();
    glAttachShader(handle_, vs);
    glAttachShader(handle_, fs);
    glLinkProgram(handle_);

    int success = 0;
    glGetProgramiv(handle_, GL_LINK_STATUS, &success);
    if (!success) {
        char log[1024];
        glGetProgramInfoLog(handle_, sizeof(log), nullptr, log);
        GE_LOG_ERROR("Program link error: %s", log);
        glDeleteProgram(handle_);
        handle_ = 0;
        return false;
    }

    glDeleteShader(vs);
    glDeleteShader(fs);
    valid_ = true;
    return true;
}

void ShaderProgram::use() const {
    glUseProgram(handle_);
}

void ShaderProgram::set_mat4(const char* name, const float* value) {
    glUniformMatrix4fv(glGetUniformLocation(handle_, name), 1, GL_FALSE, value);
}

void ShaderProgram::set_vec4(const char* name, const float* value) {
    glUniform4fv(glGetUniformLocation(handle_, name), 1, value);
}

}  // namespace ge
