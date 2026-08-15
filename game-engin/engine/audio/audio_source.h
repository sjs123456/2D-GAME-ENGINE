#pragma once

#include <string>

#include "audio/audio_manager.h"
#include "ecs/component.h"
#include "ecs/gameobject.h"
#include "render/camera.h"

namespace ge {

class AudioSource : public Component {
public:
    std::string sound;
    bool play_on_collision = false;
    bool loop = false;
    float volume = 1.0f;
    float range = 800.0f;
    bool spatial = true;
    Camera2D* listener = nullptr;

    void play() {
        if (sound.empty()) {
            return;
        }
        if (spatial && listener) {
            g_audio().play_sfx_at(sound, owner()->transform.pos, listener->position(),
                                  range, volume);
        } else {
            g_audio().play_sfx(sound, volume, loop);
        }
    }

    void OnCollisionEnter(const CollisionInfo& info) override {
        if (!play_on_collision || sound.empty()) {
            return;
        }
        const float impact = std::clamp(info.impact_speed / 700.0f, 0.0f, 1.0f);
        if (impact < 0.02f) {
            return;
        }
        if (spatial && listener) {
            g_audio().play_sfx_at(sound, owner()->transform.pos, listener->position(),
                                  range, volume * impact);
        } else {
            g_audio().play_sfx(sound, volume * impact, loop);
        }
    }
};

}  // namespace ge
