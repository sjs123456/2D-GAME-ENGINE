#pragma once

#include <deque>
#include <string>
#include <vector>

#include <SDL.h>

#include "core/logger.h"
#include "core/math.h"
#include "ecs/scene.h"
#include "render/camera.h"
#include "render/renderer2d.h"

struct SDL_Window;

namespace ge {

class EditorApp {
public:
    EditorApp() = default;
    ~EditorApp();
    EditorApp(const EditorApp&) = delete;
    EditorApp& operator=(const EditorApp&) = delete;

    bool init(SDL_Window* window, SDL_GLContext context);
    void shutdown();

    void process_events(const std::vector<SDL_Event>& events);
    void begin_viewport(int fb_width, int fb_height);
    void end_viewport();
    void draw(Scene& scene, Camera2D& camera, float fps, unsigned int sprites,
              unsigned int draw_calls);

    bool simulation_playing() const { return playing_; }
    bool consume_step_request() {
        const bool r = pending_step_;
        pending_step_ = false;
        return r;
    }
    void viewport_size(int& width, int& height) const {
        width = last_vp_width_;
        height = last_vp_height_;
    }
    void clear_selection() { selected_ = nullptr; }

    static EditorApp& instance();
    static bool enabled();

private:
    void draw_toolbar(Scene& scene, float fps, unsigned int sprites, unsigned int draw_calls);
    void draw_hierarchy(Scene& scene);
    void draw_inspector(Scene& scene, Camera2D& camera);
    void draw_assets(Scene& scene);
    void draw_console();
    void draw_viewport(Scene& scene, Camera2D& camera);

    GameObject* pick_entity(const Scene& scene, Vec2 world) const;

    unsigned int fbo_ = 0;
    unsigned int fbo_texture_ = 0;
    unsigned int fbo_depth_ = 0;
    int fbo_width_ = 0;
    int fbo_height_ = 0;

    GameObject* selected_ = nullptr;
    std::string rename_buffer_;
    bool renaming_ = false;
    bool playing_ = false;
    bool pending_step_ = false;
    int last_vp_width_ = 1280;
    int last_vp_height_ = 720;

    std::deque<std::pair<LogLevel, std::string>> console_lines_;
    std::vector<std::string> prefab_files_;
    std::vector<std::string> texture_files_;
    int instantiate_counter_ = 0;
    int spawn_counter_ = 0;
    int add_component_type_ = 0;
};

}  // namespace ge
