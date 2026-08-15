#pragma once

#include <SDL.h>

#include <string>
#include <unordered_map>
#include <vector>

namespace ge {

class InputManager;

class InputMap {
public:
    void bind(const std::string& action, SDL_Scancode key);
    bool load_from_file(const std::string& path);

    bool is_down(const std::string& action) const;
    bool is_pressed(const std::string& action) const;
    bool is_released(const std::string& action) const;

private:
    std::unordered_map<std::string, std::vector<SDL_Scancode>> actions_;
};

}  // namespace ge
