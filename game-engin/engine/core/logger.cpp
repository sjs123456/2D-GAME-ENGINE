#include "core/logger.h"

#include <chrono>
#include <ctime>

#ifdef _WIN32
#include <windows.h>
#endif

namespace ge {

namespace {

const char* level_tag(LogLevel level) {
    switch (level) {
        case LogLevel::Debug: return "DEBUG";
        case LogLevel::Info:  return "INFO ";
        case LogLevel::Warn:  return "WARN ";
        case LogLevel::Error: return "ERROR";
    }
    return "?????";
}

}  // namespace

Logger& Logger::instance() {
    static Logger logger;
    return logger;
}

Logger::Logger() {
#ifdef _WIN32
    HANDLE console = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD mode = 0;
    if (console != INVALID_HANDLE_VALUE && GetConsoleMode(console, &mode)) {
        SetConsoleMode(console, mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
    }
#endif
}

Logger::~Logger() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (file_) {
        std::fclose(file_);
    }
}

void Logger::open_file(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (file_) {
        std::fclose(file_);
    }
    file_ = std::fopen(path.c_str(), "a");
}

void Logger::set_min_level(LogLevel level) {
    min_level_ = level;
}

void Logger::log(LogLevel level, const char* file, int line, const std::string& message) {
    if (static_cast<int>(level) < static_cast<int>(min_level_)) {
        return;
    }

    const auto now = std::chrono::system_clock::now();
    const std::time_t t = std::chrono::system_clock::to_time_t(now);
    std::tm tm_buf{};
#ifdef _WIN32
    localtime_s(&tm_buf, &t);
#else
    localtime_r(&t, &tm_buf);
#endif

    char stamp[32];
    std::snprintf(stamp, sizeof(stamp), "%02d:%02d:%02d", tm_buf.tm_hour, tm_buf.tm_min, tm_buf.tm_sec);

    std::lock_guard<std::mutex> lock(mutex_);
    std::printf("[%s] [%s] %s:%d %s\n", stamp, level_tag(level), file, line, message.c_str());
    if (file_) {
        std::fprintf(file_, "[%s] [%s] %s:%d %s\n", stamp, level_tag(level), file, line, message.c_str());
        std::fflush(file_);
    }
    if (sink_) {
        sink_(level, message);
    }
}

}  // namespace ge
