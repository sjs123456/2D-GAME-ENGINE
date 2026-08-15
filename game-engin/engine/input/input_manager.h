#pragma once

#include <SDL.h>

#include <vector>

#include "core/math.h"

namespace ge {

class InputManager {
public:
    void update(const std::vector<SDL_Event>& events);

    bool is_down(SDL_Scancode key) const;
    bool is_pressed(SDL_Scancode key) const;
    bool is_released(SDL_Scancode key) const;

    bool mouse_down(int button) const;
    bool mouse_pressed(int button) const;
    bool mouse_released(int button) const;
    Vec2 mouse_position() const { return mouse_pos_; }
    Vec2 mouse_delta() const { return mouse_delta_; }
    float mouse_scroll() const { return scroll_; }
    void reset_scroll() { scroll_ = 0.0f; }

private:
    bool keys_down_[SDL_NUM_SCANCODES] = {false};
    bool keys_pressed_[SDL_NUM_SCANCODES] = {false};
    bool keys_released_[SDL_NUM_SCANCODES] = {false};
    bool mouse_down_[8] = {false};
    bool mouse_pressed_[8] = {false};
    bool mouse_released_[8] = {false};
    Vec2 mouse_pos_{0.0f, 0.0f};
    Vec2 mouse_delta_{0.0f, 0.0f};
    float scroll_ = 0.0f;
};

InputManager& g_input();
void bind_input(InputManager* input);

}  // namespace ge
