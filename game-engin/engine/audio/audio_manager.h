#pragma once

#include <string>
#include <unordered_map>

#include "core/math.h"

struct Mix_Chunk;

namespace ge {

class AudioManager {
public:
    static AudioManager& instance();

    bool init(int channels = 32);
    void shutdown();

    bool load_sfx(const std::string& name, const std::string& path);

    void play_sfx(const std::string& name, float volume = 1.0f, bool loop = false);
    void play_sfx_at(const std::string& name, Vec2 world_pos, Vec2 listener_pos,
                     float range, float volume = 1.0f);

    void play_music(const std::string& path, float fade_ms = 0.0f);
    void stop_music(float fade_ms = 0.0f);
    void set_music_volume(float volume);
    void set_sfx_volume(float volume);

    unsigned int playing_channels() const;
    bool initialized() const { return initialized_; }

private:
    AudioManager() = default;
    ~AudioManager();
    AudioManager(const AudioManager&) = delete;
    AudioManager& operator=(const AudioManager&) = delete;

    std::unordered_map<std::string, Mix_Chunk*> sfx_;
    float sfx_volume_ = 1.0f;
    bool initialized_ = false;
};

AudioManager& g_audio();

}  // namespace ge
