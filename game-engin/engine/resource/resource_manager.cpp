#include "resource/resource_manager.h"

#include <stb_image.h>

#include <algorithm>
#include <cmath>

#include "core/logger.h"

namespace ge {

namespace {
constexpr int kWorkerCount = 2;

bool decode_image(const std::string& path, int& width, int& height,
                  std::vector<unsigned char>& pixels) {
    stbi_set_flip_vertically_on_load(1);
    int w = 0;
    int h = 0;
    int channels = 0;
    unsigned char* data = stbi_load(path.c_str(), &w, &h, &channels, 4);
    if (!data) {
        return false;
    }
    width = w;
    height = h;
    pixels.assign(data, data + static_cast<size_t>(w) * h * 4);
    stbi_image_free(data);
    return true;
}
}  // namespace

ResourceManager& ResourceManager::instance() {
    static ResourceManager manager;
    return manager;
}

ResourceManager::ResourceManager() {
    for (int i = 0; i < kWorkerCount; ++i) {
        workers_.emplace_back([this]() {
            while (true) {
                std::shared_ptr<AsyncJob> job;
                {
                    std::lock_guard<std::mutex> lock(queue_mutex_);
                    if (job_queue_.empty()) {
                        if (stop_workers_.load()) {
                            return;
                        }
                        continue;
                    }
                    job = job_queue_.front();
                    job_queue_.pop_front();
                }
                if (!decode_image(job->full_path, job->width, job->height, job->pixels)) {
                    job->failed.store(true);
                }
                job->ready.store(true);
            }
        });
    }
}

ResourceManager::~ResourceManager() {
    stop_workers_.store(true);
    for (std::thread& t : workers_) {
        if (t.joinable()) {
            t.join();
        }
    }
}

std::string ResourceManager::resolve(const std::string& path) const {
    return root_ + "/" + path;
}

ResourceManager::Entry* ResourceManager::find_or_create(const std::string& path) {
    const auto it = entries_.find(path);
    if (it != entries_.end()) {
        return it->second;
    }
    storage_.push_back(std::make_unique<Entry>());
    Entry* entry = storage_.back().get();
    entry->full_path = resolve(path);
    entry->texture = std::make_unique<Texture>();
    entries_[path] = entry;
    return entry;
}

Texture* ResourceManager::load_texture(const std::string& path) {
    Entry* entry = find_or_create(path);
    if (entry->texture->valid()) {
        ++entry->refs;
        return entry->texture.get();
    }
    if (!entry->texture->load(entry->full_path)) {
        GE_LOG_ERROR("ResourceManager: failed to load '%s'", path.c_str());
        return nullptr;
    }
    std::error_code ec;
    entry->mtime = std::filesystem::last_write_time(entry->full_path, ec);
    ++entry->refs;
    GE_LOG_INFO("ResourceManager: loaded '%s' (refs=%d)", path.c_str(), entry->refs);
    return entry->texture.get();
}

void ResourceManager::unload_texture(const std::string& path) {
    const auto it = entries_.find(path);
    if (it == entries_.end()) {
        return;
    }
    Entry* entry = it->second;
    if (entry->refs > 0) {
        --entry->refs;
    }
    if (entry->refs == 0) {
        entry->texture->destroy();
        entry->mtime = {};
    }
}

void ResourceManager::reload_entry(Entry& entry) {
    if (!entry.texture->load(entry.full_path)) {
        GE_LOG_ERROR("ResourceManager: reload failed for '%s'", entry.full_path.c_str());
        return;
    }
    std::error_code ec;
    entry.mtime = std::filesystem::last_write_time(entry.full_path, ec);
    if (hot_reload_cb_) {
        hot_reload_cb_(entry.full_path);
    }
}

void ResourceManager::reload_texture(const std::string& path) {
    const auto it = entries_.find(path);
    if (it != entries_.end()) {
        reload_entry(*it->second);
    }
}

void ResourceManager::load_texture_async(const std::string& path,
                                         std::function<void(Texture*, bool)> on_done) {
    auto job = std::make_shared<AsyncJob>();
    job->path = path;
    job->full_path = resolve(path);
    job->on_done = std::move(on_done);
    pending_.push_back(job);
    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        job_queue_.push_back(job);
    }
}

void ResourceManager::process_async() {
    auto it = pending_.begin();
    while (it != pending_.end()) {
        const std::shared_ptr<AsyncJob>& job = *it;
        if (!job->ready.load()) {
            ++it;
            continue;
        }
        Texture* texture = nullptr;
        bool ok = false;
        if (!job->failed.load() && !job->pixels.empty()) {
            Entry* entry = find_or_create(job->path);
            if (entry->texture->create_from_pixels(job->width, job->height, job->pixels.data())) {
                std::error_code ec;
                entry->mtime = std::filesystem::last_write_time(entry->full_path, ec);
                texture = entry->texture.get();
                ok = true;
                GE_LOG_INFO("ResourceManager: async loaded '%s'", job->path.c_str());
            }
        }
        if (job->on_done) {
            job->on_done(texture, ok);
        }
        it = pending_.erase(it);
    }
}

void ResourceManager::poll_hot_reload() {
    for (const auto& [path, entry] : entries_) {
        if (!entry->texture->valid()) {
            continue;
        }
        std::error_code ec;
        const auto mtime = std::filesystem::last_write_time(entry->full_path, ec);
        if (ec || mtime == entry->mtime) {
            continue;
        }
        GE_LOG_INFO("ResourceManager: '%s' changed on disk, reloading", path.c_str());
        reload_entry(*entry);
    }
}

Texture* ResourceManager::builtin_white() {
    if (!builtin_white_) {
        builtin_white_ = std::make_unique<Texture>();
        const unsigned char white[4] = {255, 255, 255, 255};
        builtin_white_->create_from_pixels(1, 1, white);
    }
    return builtin_white_.get();
}

Texture* ResourceManager::builtin_circle() {
    if (!builtin_circle_) {
        builtin_circle_ = std::make_unique<Texture>();
        constexpr int kSize = 64;
        std::vector<unsigned char> pixels(kSize * kSize * 4);
        const float radius = kSize * 0.5f - 1.0f;
        for (int y = 0; y < kSize; ++y) {
            for (int x = 0; x < kSize; ++x) {
                const float dx = x + 0.5f - kSize * 0.5f;
                const float dy = y + 0.5f - kSize * 0.5f;
                const float dist = std::sqrt(dx * dx + dy * dy);
                const float alpha = std::clamp(radius - dist, 0.0f, 1.0f);
                const int idx = (y * kSize + x) * 4;
                pixels[idx + 0] = 255;
                pixels[idx + 1] = 255;
                pixels[idx + 2] = 255;
                pixels[idx + 3] = static_cast<unsigned char>(alpha * 255.0f);
            }
        }
        builtin_circle_->create_from_pixels(kSize, kSize, pixels.data());
    }
    return builtin_circle_.get();
}

}  // namespace ge
