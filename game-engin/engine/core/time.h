#pragma once

#include <chrono>

namespace ge {

class TickTimer {
public:
    TickTimer() {
        reset();
    }

    void reset() {
        start_ = clock::now();
        last_ = start_;
        elapsed_ = 0.0;
        fps_ = 0.0;
    }

    double tick() {
        const auto now = clock::now();
        const double dt = std::chrono::duration<double>(now - last_).count();
        last_ = now;
        elapsed_ += dt;
        if (dt > 0.0) {
            const double instant = 1.0 / dt;
            fps_ = (fps_ == 0.0) ? instant : fps_ + (instant - fps_) * 0.05;
        }
        return dt;
    }

    double elapsed() const { return elapsed_; }
    double fps() const { return fps_; }

private:
    using clock = std::chrono::steady_clock;

    clock::time_point start_;
    clock::time_point last_;
    double elapsed_ = 0.0;
    double fps_ = 0.0;
};

}  // namespace ge
