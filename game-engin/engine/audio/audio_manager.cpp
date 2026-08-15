#include "audio/audio_manager.h"

#include <SDL_mixer.h>

#include <algorithm>
#include <cmath>

#include "core/logger.h"

namespace ge {

AudioManager& AudioManager::instance() {
    static AudioManager manager;
    return manager;
}

AudioManager& g_audio() {
    return AudioManager::instance();
}

AudioManager::~AudioManager() {
    shutdown();
}

bool AudioManager::init(int channels) {
    if (initialized_) {
        return true;
    }
    if (Mix_OpenAudio(22050, MIX_DEFAULT_FORMAT, 2, 512) != 0) {
        GE_LOG_ERROR("AudioManager: Mix_OpenAudio failed: %s", Mix_GetError());
        return false;
    }
    if (Mix_AllocateChannels(channels) != channels) {
        GE_LOG_WARN("AudioManager: allocated %d channels", Mix_AllocateChannels(-1));
    }
    initialized_ = true;
    GE_LOG_INFO("AudioManager initialized (%d channels)", channels);
    return true;
}

void AudioManager::shutdown() {
    if (!initialized_) {
        return;
    }
    for (auto& [name, chunk] : sfx_) {
        Mix_FreeChunk(chunk);
    }
    sfx_.clear();
    Mix_HaltMusic();
    Mix_CloseAudio();
    initialized_ = false;
}

bool AudioManager::load_sfx(const std::string& name, const std::string& path) {
    const auto it = sfx_.find(name);
    if (it != sfx_.end()) {
        return true;
    }
    Mix_Chunk* chunk = Mix_LoadWAV(path.c_str());
    if (!chunk) {
        GE_LOG_ERROR("AudioManager: failed to load '%s': %s", path.c_str(), Mix_GetError());
        return false;
    }
    sfx_[name] = chunk;
    GE_LOG_INFO("AudioManager: loaded sfx '%s' from '%s'", name.c_str(), path.c_str());
    return true;
}

void AudioManager::play_sfx(const std::string& name, float volume, bool loop) {
    const auto it = sfx_.find(name);
    if (it == sfx_.end()) {
        GE_LOG_WARN("AudioManager: unknown sfx '%s'", name.c_str());
        return;
    }
    const int channel = Mix_PlayChannel(-1, it->second, loop ? -1 : 0);
    if (channel < 0) {
        return;
    }
    Mix_Volume(channel, static_cast<int>(volume * sfx_volume_ * MIX_MAX_VOLUME));
}

void AudioManager::play_sfx_at(const std::string& name, Vec2 world_pos, Vec2 listener_pos,
                               float range, float volume) {
    const auto it = sfx_.find(name);
    if (it == sfx_.end() || range <= 0.0f) {
        return;
    }
    const Vec2 delta = world_pos - listener_pos;
    const float dist = std::sqrt(delta.x * delta.x + delta.y * delta.y);
    if (dist > range) {
        return;
    }
    const float dist_scale = 1.0f - dist / range;
    const float pan = std::clamp(delta.x / range, -1.0f, 1.0f);
    const int left = static_cast<int>(255.0f * (1.0f - pan) * 0.5f);
    const int right = static_cast<int>(255.0f * (1.0f + pan) * 0.5f);

    const int channel = Mix_PlayChannel(-1, it->second, 0);
    if (channel < 0) {
        return;
    }
    Mix_Volume(channel, static_cast<int>(volume * dist_scale * sfx_volume_ * MIX_MAX_VOLUME));
    Mix_SetPanning(channel, static_cast<unsigned char>(left), static_cast<unsigned char>(right));
}

void AudioManager::play_music(const std::string& path, float fade_ms) {
    Mix_Music* music = Mix_LoadMUS(path.c_str());
    if (!music) {
        GE_LOG_ERROR("AudioManager: failed to load music '%s': %s", path.c_str(), Mix_GetError());
        return;
    }
    if (fade_ms > 0.0f) {
        Mix_FadeInMusic(music, -1, static_cast<int>(fade_ms));
    } else {
        Mix_PlayMusic(music, -1);
    }
    GE_LOG_INFO("AudioManager: playing music '%s'", path.c_str());
}

void AudioManager::stop_music(float fade_ms) {
    if (fade_ms > 0.0f) {
        Mix_FadeOutMusic(static_cast<int>(fade_ms));
    } else {
        Mix_HaltMusic();
    }
}

void AudioManager::set_music_volume(float volume) {
    Mix_VolumeMusic(static_cast<int>(std::clamp(volume, 0.0f, 1.0f) * MIX_MAX_VOLUME));
}

void AudioManager::set_sfx_volume(float volume) {
    sfx_volume_ = std::clamp(volume, 0.0f, 1.0f);
}

unsigned int AudioManager::playing_channels() const {
    if (!initialized_) {
        return 0;
    }
    return static_cast<unsigned int>(Mix_Playing(-1));
}

}  // namespace ge
