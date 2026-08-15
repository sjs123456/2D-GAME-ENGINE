#include "input/input_map.h"

#include <fstream>
#include <sstream>

#include "core/logger.h"
#include "input/input_manager.h"

namespace ge {

namespace {

SDL_Scancode find_scancode(const std::string& name) {
    for (int i = 0; i < SDL_NUM_SCANCODES; ++i) {
        if (SDL_strcasecmp(name.c_str(), SDL_GetScancodeName(static_cast<SDL_Scancode>(i))) == 0) {
            return static_cast<SDL_Scancode>(i);
        }
    }
    return SDL_SCANCODE_UNKNOWN;
}

std::vector<SDL_Scancode> parse_keys(const std::string& rest) {
    std::vector<SDL_Scancode> keys;
    size_t start = 0;
    while (start < rest.size()) {
        while (start < rest.size() && rest[start] == ' ') {
            ++start;
        }
        if (start >= rest.size()) {
            break;
        }
        size_t end = start + 1;
        SDL_Scancode best = SDL_SCANCODE_UNKNOWN;
        size_t best_len = 0;
        while (end <= rest.size()) {
            const std::string candidate = rest.substr(start, end - start);
            const SDL_Scancode code = find_scancode(candidate);
            if (code != SDL_SCANCODE_UNKNOWN) {
                best = code;
                best_len = end - start;
            }
            ++end;
            if (end - start > 32) {
                break;
            }
        }
        if (best == SDL_SCANCODE_UNKNOWN) {
            break;
        }
        keys.push_back(best);
        start += best_len;
    }
    return keys;
}

}  // namespace

void InputMap::bind(const std::string& action, SDL_Scancode key) {
    actions_[action].push_back(key);
}

bool InputMap::load_from_file(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        GE_LOG_ERROR("InputMap: cannot open '%s'", path.c_str());
        return false;
    }

    std::string line;
    while (std::getline(file, line)) {
        if (line.empty() || line[0] == '#') {
            continue;
        }
        const size_t first = line.find_first_not_of(' ');
        if (first == std::string::npos) {
            continue;
        }
        const std::string trimmed = line.substr(first);
        std::istringstream iss(trimmed);
        std::string action;
        iss >> action;
        if (action.empty()) {
            continue;
        }
        const std::string rest = trimmed.substr(action.size());
        const std::vector<SDL_Scancode> keys = parse_keys(rest);
        if (keys.empty()) {
            GE_LOG_WARN("InputMap: no valid keys for action '%s'", action.c_str());
            continue;
        }
        for (const SDL_Scancode key : keys) {
            bind(action, key);
        }
    }

    GE_LOG_INFO("InputMap loaded %zu actions from '%s'", actions_.size(), path.c_str());
    return true;
}

bool InputMap::is_down(const std::string& action) const {
    const auto it = actions_.find(action);
    if (it == actions_.end()) {
        return false;
    }
    for (const SDL_Scancode key : it->second) {
        if (g_input().is_down(key)) {
            return true;
        }
    }
    return false;
}

bool InputMap::is_pressed(const std::string& action) const {
    const auto it = actions_.find(action);
    if (it == actions_.end()) {
        return false;
    }
    for (const SDL_Scancode key : it->second) {
        if (g_input().is_pressed(key)) {
            return true;
        }
    }
    return false;
}

bool InputMap::is_released(const std::string& action) const {
    const auto it = actions_.find(action);
    if (it == actions_.end()) {
        return false;
    }
    for (const SDL_Scancode key : it->second) {
        if (g_input().is_released(key)) {
            return true;
        }
    }
    return false;
}

}  // namespace ge
