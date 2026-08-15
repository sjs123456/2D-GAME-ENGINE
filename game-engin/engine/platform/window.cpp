#include "platform/window.h"

#include <glad/glad.h>
#include <SDL.h>

#include "core/logger.h"

namespace ge {

Window::~Window() {
    shutdown();
}

bool Window::init(const Config& config) {
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_TIMER | SDL_INIT_AUDIO) != 0) {
        GE_LOG_ERROR("SDL_Init failed: %s", SDL_GetError());
        return false;
    }

    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);

    window_ = SDL_CreateWindow(config.title.c_str(),
                               SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                               config.width, config.height,
                               SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE | SDL_WINDOW_SHOWN);
    if (!window_) {
        GE_LOG_ERROR("SDL_CreateWindow failed: %s", SDL_GetError());
        shutdown();
        return false;
    }

    gl_context_ = SDL_GL_CreateContext(window_);
    if (!gl_context_) {
        GE_LOG_ERROR("SDL_GL_CreateContext failed: %s", SDL_GetError());
        shutdown();
        return false;
    }

    if (SDL_GL_SetSwapInterval(1) != 0) {
        GE_LOG_WARN("SDL_GL_SetSwapInterval failed: %s", SDL_GetError());
    }

    width_ = config.width;
    height_ = config.height;
    return true;
}

void Window::shutdown() {
    if (gl_context_) {
        SDL_GL_DeleteContext(gl_context_);
        gl_context_ = nullptr;
    }
    if (window_) {
        SDL_DestroyWindow(window_);
        window_ = nullptr;
    }
    SDL_Quit();
}

void Window::poll_events() {
    frame_events_.clear();
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        frame_events_.push_back(event);
        if (event.type == SDL_QUIT) {
            close_requested_ = true;
        } else if (event.type == SDL_WINDOWEVENT && event.window.event == SDL_WINDOWEVENT_RESIZED) {
            width_ = event.window.data1;
            height_ = event.window.data2;
            SDL_GL_MakeCurrent(window_, gl_context_);
            glViewport(0, 0, width_, height_);
        }
    }
}

void Window::swap() {
    SDL_GL_SwapWindow(window_);
}

void Window::set_title(const std::string& title) {
    SDL_SetWindowTitle(window_, title.c_str());
}

}  // namespace ge
