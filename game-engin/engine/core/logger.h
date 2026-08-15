#pragma once

#include <cstdio>
#include <functional>
#include <mutex>
#include <string>

namespace ge {

enum class LogLevel { Debug = 0, Info, Warn, Error };

class Logger {
public:
    using Sink = std::function<void(LogLevel, const std::string&)>;

    static Logger& instance();

    void open_file(const std::string& path);
    void set_min_level(LogLevel level);
    void set_sink(Sink sink) { sink_ = std::move(sink); }

    void log(LogLevel level, const char* file, int line, const std::string& message);

private:
    Logger();
    ~Logger();
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    std::FILE* file_ = nullptr;
    LogLevel min_level_ = LogLevel::Debug;
    Sink sink_;
    std::mutex mutex_;
};

}  // namespace ge

#define GE_LOG(level, ...)                                                       \
    do {                                                                         \
        char ge_buf_[1024];                                                      \
        std::snprintf(ge_buf_, sizeof(ge_buf_), __VA_ARGS__);                    \
        ::ge::Logger::instance().log(level, __FILE__, __LINE__, ge_buf_);        \
    } while (0)

#define GE_LOG_DEBUG(...) GE_LOG(::ge::LogLevel::Debug, __VA_ARGS__)
#define GE_LOG_INFO(...) GE_LOG(::ge::LogLevel::Info, __VA_ARGS__)
#define GE_LOG_WARN(...) GE_LOG(::ge::LogLevel::Warn, __VA_ARGS__)
#define GE_LOG_ERROR(...) GE_LOG(::ge::LogLevel::Error, __VA_ARGS__)
