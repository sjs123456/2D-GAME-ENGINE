#pragma once

#include <atomic>
#include <deque>
#include <filesystem>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include "render/texture.h"

namespace ge {

class ResourceManager {
public:
    static ResourceManager& instance();

    ResourceManager();
    ~ResourceManager();
    ResourceManager(const ResourceManager&) = delete;
    ResourceManager& operator=(const ResourceManager&) = delete;

    void set_asset_root(const std::string& root) { root_ = root; }
    const std::string& asset_root() const { return root_; }

    Texture* load_texture(const std::string& path);
    void unload_texture(const std::string& path);
    void reload_texture(const std::string& path);

    Texture* builtin_white();
    Texture* builtin_circle();

    void load_texture_async(const std::string& path,
                            std::function<void(Texture*, bool)> on_done = nullptr);
    void process_async();

    void poll_hot_reload();
    void set_hot_reload_callback(std::function<void(const std::string&)> callback) {
        hot_reload_cb_ = std::move(callback);
    }

private:
    struct Entry {
        std::string full_path;
        std::unique_ptr<Texture> texture;
        std::filesystem::file_time_type mtime;
        int refs = 1;
    };

    struct AsyncJob {
        std::string path;
        std::string full_path;
        int width = 0;
        int height = 0;
        std::vector<unsigned char> pixels;
        std::atomic<bool> ready{false};
        std::atomic<bool> failed{false};
        std::function<void(Texture*, bool)> on_done;
    };

    Entry* find_or_create(const std::string& path);
    void reload_entry(Entry& entry);
    std::string resolve(const std::string& path) const;

    std::string root_ = "assets";
    std::unordered_map<std::string, Entry*> entries_;
    std::deque<std::unique_ptr<Entry>> storage_;
    std::mutex queue_mutex_;
    std::deque<std::shared_ptr<AsyncJob>> job_queue_;
    std::vector<std::shared_ptr<AsyncJob>> pending_;
    std::vector<std::thread> workers_;
    std::atomic<bool> stop_workers_{false};
    std::function<void(const std::string&)> hot_reload_cb_;

    std::unique_ptr<Texture> builtin_white_;
    std::unique_ptr<Texture> builtin_circle_;
};

}  // namespace ge
