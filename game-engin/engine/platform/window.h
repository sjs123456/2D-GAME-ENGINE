#pragma once

#include <string>
#include <vector>

struct SDL_Window;
typedef void* SDL_GLContext;
union SDL_Event;

namespace ge {

class Window {
public:
    struct Config {
        int width = 1280;
        int height = 720;
        std::string title = "Game Engine";
    };

    Window() = default;
    ~Window();
    Window(const Window&) = delete;
    Window& operator=(const Window&) = delete;

    bool init(const Config& config);
    void shutdown();

    void poll_events();
    void swap();
    void set_title(const std::string& title);
    void request_close() { close_requested_ = true; }

    bool should_close() const { return close_requested_; }
    int width() const { return width_; }
    int height() const { return height_; }
    SDL_Window* sdl_window() const { return window_; }
    SDL_GLContext sdl_gl_context() const { return gl_context_; }
    const std::vector<SDL_Event>& frame_events() const { return frame_events_; }

private:
    SDL_Window* window_ = nullptr;
    SDL_GLContext gl_context_ = nullptr;
    bool close_requested_ = false;
    int width_ = 0;
    int height_ = 0;
    std::vector<SDL_Event> frame_events_;
};

}  // namespace ge
