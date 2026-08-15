#include "input/input_manager.h"

#include <algorithm>

namespace ge {

namespace {
InputManager* s_input = nullptr;
}

InputManager& g_input() {
    static InputManager fallback;
    return s_input ? *s_input : fallback;
}

void bind_input(InputManager* input) {
    s_input = input;
}

void InputManager::update(const std::vector<SDL_Event>& events) {
    std::fill(std::begin(keys_pressed_), std::end(keys_pressed_), false);
    std::fill(std::begin(keys_released_), std::end(keys_released_), false);
    std::fill(std::begin(mouse_pressed_), std::end(mouse_pressed_), false);
    std::fill(std::begin(mouse_released_), std::end(mouse_released_), false);
    mouse_delta_ = {0.0f, 0.0f};

    for (const SDL_Event& e : events) {
        switch (e.type) {
            case SDL_KEYDOWN:
                if (e.key.repeat == 0 && e.key.keysym.scancode < SDL_NUM_SCANCODES) {
                    const int s = e.key.keysym.scancode;
                    keys_down_[s] = true;
                    keys_pressed_[s] = true;
                }
                break;
            case SDL_KEYUP:
                if (e.key.keysym.scancode < SDL_NUM_SCANCODES) {
                    const int s = e.key.keysym.scancode;
                    keys_down_[s] = false;
                    keys_released_[s] = true;
                }
                break;
            case SDL_MOUSEBUTTONDOWN: {
                const int b = e.button.button - 1;
                if (b >= 0 && b < 8) {
                    mouse_down_[b] = true;
                    mouse_pressed_[b] = true;
                }
                break;
            }
            case SDL_MOUSEBUTTONUP: {
                const int b = e.button.button - 1;
                if (b >= 0 && b < 8) {
                    mouse_down_[b] = false;
                    mouse_released_[b] = true;
                }
                break;
            }
            case SDL_MOUSEMOTION:
                mouse_pos_ = {static_cast<float>(e.motion.x), static_cast<float>(e.motion.y)};
                mouse_delta_.x += static_cast<float>(e.motion.xrel);
                mouse_delta_.y += static_cast<float>(e.motion.yrel);
                break;
            case SDL_MOUSEWHEEL: {
                float y = static_cast<float>(e.wheel.y);
                if (e.wheel.direction == SDL_MOUSEWHEEL_FLIPPED) {
                    y = -y;
                }
                scroll_ += y;
                break;
            }
            default:
                break;
        }
    }
}

bool InputManager::is_down(SDL_Scancode key) const {
    return key < SDL_NUM_SCANCODES && keys_down_[key];
}

bool InputManager::is_pressed(SDL_Scancode key) const {
    return key < SDL_NUM_SCANCODES && keys_pressed_[key];
}

bool InputManager::is_released(SDL_Scancode key) const {
    return key < SDL_NUM_SCANCODES && keys_released_[key];
}

bool InputManager::mouse_down(int button) const {
    return button > 0 && button <= 8 && mouse_down_[button - 1];
}

bool InputManager::mouse_pressed(int button) const {
    return button > 0 && button <= 8 && mouse_pressed_[button - 1];
}

bool InputManager::mouse_released(int button) const {
    return button > 0 && button <= 8 && mouse_released_[button - 1];
}

}  // namespace ge
