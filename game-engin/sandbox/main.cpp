#define SDL_MAIN_HANDLED
#include <glad/glad.h>
#include <SDL.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <set>
#include <string>

#include "audio/audio_manager.h"
#include "audio/audio_source.h"
#include "core/logger.h"
#include "core/math.h"
#include "core/time.h"
#include "ecs/component.h"
#include "ecs/gameobject.h"
#include "ecs/scene.h"
#include "input/input_manager.h"
#include "input/input_map.h"
#include "physics/collider.h"
#include "physics/physics_world.h"
#include "physics/rigidbody.h"
#include "platform/window.h"
#include "render/camera.h"
#include "render/renderer2d.h"
#include "render/sprite_renderer.h"
#include "render/texture_atlas.h"
#include "resource/resource_manager.h"
#include "scene/prefab.h"
#include "scene/serializer.h"

#ifdef GE_BUILD_EDITOR
#include <imgui.h>
#include <imgui_impl_opengl3.h>
#include "editor/editor_app.h"
#endif

namespace {

constexpr float kFixedDt = 1.0f / 60.0f;
constexpr float kMaxDt = 0.25f;
constexpr float kTile = 32.0f;
const char* kLevelPath = "assets/scenes/mario_level.json";
constexpr float kFlagX = 112.0f * kTile + 16.0f;

struct GameState {
    int score = 0;
    int coins = 0;
    int lives = 3;
    bool won = false;
    bool game_over = false;
};

GameState g_state;
bool g_autotest = false;

ge::TextureAtlas* g_atlas = nullptr;
ge::Camera2D* g_camera = nullptr;

// ---------------------------------------------------------------- helpers

void play_sfx(const char* name, float volume = 1.0f) {
    ge::g_audio().play_sfx(name, volume, false);
}

void set_frame(ge::SpriteRenderer* spr, const char* frame_name) {
    if (const ge::UvRect* f = g_atlas->frame(frame_name)) {
        spr->uv = *f;
    }
}

ge::GameObject* spawn_entity(ge::Scene& scene, const char* id, const char* prefab,
                             float x, float y, float sx, float sy) {
    ge::prefab::instantiate(std::string("prefabs/") + prefab + ".json", scene, id);
    if (ge::GameObject* go = scene.FindByName(id)) {
        go->transform.pos = {x, y};
        go->transform.scale = {sx, sy};
        return go;
    }
    return nullptr;
}

// ---------------------------------------------------------------- components

class EnemyWalker : public ge::Component {
public:
    float speed = 55.0f;
    float dir = -1.0f;
    const char* frames[2] = {"goomba_1", "goomba_2"};
    bool is_koopa = false;
    bool squashed = false;
    float anim_t = 0.0f;
    float squash_t = 0.0f;

    void OnInit() override {
        if (is_koopa) {
            frames[0] = "koopa_1";
            frames[1] = "koopa_2";
        }
        if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
            set_frame(spr, frames[0]);
        }
    }

    void OnUpdate(float dt) override {
        if (squashed) {
            squash_t -= dt;
            if (squash_t <= 0.0f) {
                owner()->Destroy();
            }
            return;
        }
        anim_t += dt;
        if (ge::RigidBody* rb = owner()->GetComponent<ge::RigidBody>()) {
            rb->velocity.x = dir * speed;
        }
        if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
            set_frame(spr, frames[(static_cast<int>(anim_t * 6)) % 2]);
        }
    }

    void OnCollisionEnter(const ge::CollisionInfo& info) override {
        if (squashed) {
            return;
        }
        if (std::abs(info.normal.x) > 0.5f) {
            dir = -dir;
        }
    }

    void squash() {
        squashed = true;
        squash_t = 0.45f;
        owner()->transform.scale.y = 8.0f;
        if (ge::RigidBody* rb = owner()->GetComponent<ge::RigidBody>()) {
            rb->velocity = {0.0f, 0.0f};
            rb->is_static = true;
        }
    }
};

class CoinPickup : public ge::Component {
public:
    void OnInit() override {
        if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
            set_frame(spr, "coin_1");
        }
    }

    void OnUpdate(float dt) override {
        anim_t += dt;
        if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
            set_frame(spr, (static_cast<int>(anim_t * 8)) % 2 ? "coin_2" : "coin_1");
        }
    }

    void OnCollisionEnter(const ge::CollisionInfo& info) override {
        if (info.other && info.other->name() == "Player") {
            collect();
        }
    }

    void collect() {
        g_state.score += 100;
        g_state.coins += 1;
        play_sfx("coin");
        GE_LOG_INFO("Coin! score=%d coins=%d", g_state.score, g_state.coins);
        owner()->Destroy();
    }

private:
    float anim_t = 0.0f;
};

class CoinPopup : public ge::Component {
public:
    void OnInit() override {
        if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
            set_frame(spr, "coin_1");
        }
        if (ge::RigidBody* rb = owner()->GetComponent<ge::RigidBody>()) {
            rb->velocity = {0.0f, 420.0f};
        }
    }

    void OnUpdate(float dt) override {
        alive_t += dt;
        if (alive_t > 0.55f && collectible) {
            ge::GameObject* player = nullptr;
            (void)player;
        }
        anim_t += dt;
        if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
            set_frame(spr, (static_cast<int>(anim_t * 8)) % 2 ? "coin_2" : "coin_1");
        }
    }

    void OnCollisionEnter(const ge::CollisionInfo& info) override {
        if (alive_t < 0.6f) {
            return;
        }
        if (info.other && info.other->name() == "Player") {
            g_state.score += 100;
            g_state.coins += 1;
            play_sfx("coin");
            owner()->Destroy();
        }
    }

private:
    float alive_t = 0.0f;
    float anim_t = 0.0f;
    bool collectible = true;
};

class BlockController : public ge::Component {
public:
    bool is_question = false;
    bool used = false;
    bool bumped = false;
    float bump_t = 0.0f;
    ge::Vec2 base_pos{0.0f, 0.0f};
    ge::Scene* scene = nullptr;

    void OnInit() override {
        base_pos = owner()->transform.pos;
        is_question = owner()->name().rfind("question", 0) == 0;
        if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
            set_frame(spr, is_question ? "question" : "brick");
        }
    }

    void OnUpdate(float dt) override {
        if (bumped) {
            bump_t += dt;
            const float p = std::min(bump_t / 0.18f, 1.0f);
            owner()->transform.pos.y = base_pos.y + std::sin(p * 3.14159f) * 10.0f;
            if (p >= 1.0f) {
                owner()->transform.pos.y = base_pos.y;
                bumped = false;
            }
        }
    }

    void bump() {
        if (bumped) {
            return;
        }
        bumped = true;
        bump_t = 0.0f;
        if (is_question && !used) {
            used = true;
            if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
                set_frame(spr, "block_used");
            }
            g_state.score += 100;
            play_sfx("coin");
            ge::GameObject* pop = spawn_entity(*scene, "popup_coin", "coin",
                                               owner()->transform.pos.x,
                                               owner()->transform.pos.y + 32.0f,
                                               32.0f, 32.0f);
            if (pop) {
                if (ge::RigidBody* rb = pop->GetComponent<ge::RigidBody>()) {
                    rb->is_static = false;
                    rb->velocity = {0.0f, 600.0f};
                }
                pop->AddComponent<CoinPopup>();
            }
            GE_LOG_INFO("Question block! score=%d", g_state.score);
        } else if (!is_question) {
            g_state.score += 50;
            play_sfx("break");
            spawn_debris();
            owner()->Destroy();
            GE_LOG_INFO("Brick broken! score=%d", g_state.score);
        } else {
            play_sfx("bump");
        }
    }

private:
    void spawn_debris() {
        for (int i = 0; i < 4; ++i) {
            char id[24];
            std::snprintf(id, sizeof(id), "debris_%d", debris_n_++);
            ge::GameObject* d = spawn_entity(*scene, id, "ground", owner()->transform.pos.x,
                                             owner()->transform.pos.y, 12.0f, 12.0f);
            if (!d) {
                continue;
            }
            if (ge::SpriteRenderer* spr = d->GetComponent<ge::SpriteRenderer>()) {
                set_frame(spr, "debris");
            }
            if (ge::BoxCollider* box = d->GetComponent<ge::BoxCollider>()) {
                d->RemoveComponent(box);
            }
            ge::CircleCollider* col = d->AddComponent<ge::CircleCollider>();
            col->radius = 6.0f;
            ge::RigidBody* rb = d->GetComponent<ge::RigidBody>();
            if (rb) {
                rb->is_static = false;
                rb->gravity_scale = 1.4f;
                rb->restitution = 0.3f;
                const float dx = (i % 2 == 0 ? -1.0f : 1.0f) * (80.0f + i * 40.0f);
                rb->velocity = {dx, 320.0f};
            }
        }
    }

    int debris_n_ = 0;
};

class MarioController : public ge::Component {
public:
    ge::InputMap* input_map = nullptr;
    ge::Scene* scene = nullptr;
    ge::Vec2 spawn{112.0f, -80.0f};
    float move_speed = 240.0f;
    float jump_speed = 760.0f;
    float gravity_scale = 1.0f;
    bool alive = true;
    float invuln = 0.0f;
    float anim_t = 0.0f;
    float respawn_t = 0.0f;

    void OnInit() override {
        spawn = owner()->transform.pos;
        if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
            set_frame(spr, "mario_idle");
        }
    }

    void OnUpdate(float dt) override {
        if (!alive) {
            respawn_t += dt;
            if (respawn_t > 1.2f) {
                respawn();
            }
            return;
        }
        if (invuln > 0.0f) {
            invuln -= dt;
        }

        ge::RigidBody* rb = owner()->GetComponent<ge::RigidBody>();
        float dir = 0.0f;
        if (g_autotest) {
            dir = 1.0f;
        } else {
            if (input_map->is_down("move_left")) dir -= 1.0f;
            if (input_map->is_down("move_right")) dir += 1.0f;
        }
        rb->velocity.x = dir * move_speed;

        const bool jump_pressed = g_autotest ? true : input_map->is_pressed("jump");
        const bool jump_held = g_autotest ? true : input_map->is_down("jump");
        if (jump_pressed && !grounded_others_.empty()) {
            rb->velocity.y = jump_speed;
            grounded_others_.clear();
            play_sfx("jump", 0.7f);
        } else if (!jump_held && rb->velocity.y > 120.0f) {
            rb->velocity.y = 120.0f;
        }

        anim_t += dt;
        if (ge::SpriteRenderer* spr = owner()->GetComponent<ge::SpriteRenderer>()) {
            const bool on_ground = !grounded_others_.empty();
            const char* frame = "mario_idle";
            if (!on_ground) {
                frame = "mario_jump";
            } else if (dir != 0.0f) {
                frame = (static_cast<int>(anim_t * 9)) % 2 ? "mario_run1" : "mario_run2";
            }
            set_frame(spr, frame);
            if (dir != 0.0f) {
                owner()->transform.scale.x = dir > 0.0f ? 32.0f : -32.0f;
            }
        }

        if (owner()->transform.pos.y < -2000.0f) {
            die();
        }

        if (!g_state.won && owner()->transform.pos.x > kFlagX - 8.0f) {
            g_state.won = true;
            g_state.score += 1000;
            play_sfx("win");
            GE_LOG_INFO("LEVEL COMPLETE! score=%d", g_state.score);
        }
    }

    void OnCollisionEnter(const ge::CollisionInfo& info) override {
        handle(info);
    }

    void OnCollisionStay(const ge::CollisionInfo& info) override {
        handle(info);
    }

    void OnCollisionExit(const ge::CollisionInfo& info) override {
        if (info.other) {
            grounded_others_.erase(info.other);
        }
    }

    void die() {
        if (!alive) {
            return;
        }
        alive = false;
        respawn_t = 0.0f;
        --g_state.lives;
        grounded_others_.clear();
        play_sfx("die");
        GE_LOG_WARN("Mario died! lives=%d at (%.0f,%.0f)", g_state.lives,
                    owner()->transform.pos.x, owner()->transform.pos.y);
        if (g_state.lives < 0) {
            g_state.game_over = true;
            GE_LOG_WARN("GAME OVER (score=%d)", g_state.score);
        }
    }

private:
    void handle(const ge::CollisionInfo& info) {
        if (!info.other) {
            return;
        }
        const std::string& name = info.other->name();
        if (name.rfind("goomba", 0) == 0 || name.rfind("koopa", 0) == 0) {
            if (invuln > 0.0f) {
                return;
            }
            ge::RigidBody* rb = owner()->GetComponent<ge::RigidBody>();
            if (rb && rb->velocity.y < -60.0f) {
                g_state.score += 100;
                play_sfx("stomp", 0.8f);
                rb->velocity.y = 420.0f;
                if (EnemyWalker* e = info.other->GetComponent<EnemyWalker>()) {
                    e->squash();
                }
                GE_LOG_INFO("Stomp! score=%d", g_state.score);
            } else {
                die();
            }
            return;
        }
        if (name.rfind("coin", 0) == 0 || name.rfind("popup", 0) == 0) {
            return;
        }
        if (info.normal.y > 0.5f) {
            grounded_others_.insert(info.other);
        } else if (info.normal.y < -0.5f) {
            if (BlockController* block = info.other->GetComponent<BlockController>()) {
                block->bump();
            }
        }
    }

    void respawn() {
        owner()->transform.pos = spawn;
        if (ge::RigidBody* rb = owner()->GetComponent<ge::RigidBody>()) {
            rb->velocity = {0.0f, 0.0f};
            rb->at_rest = false;
        }
        alive = true;
        invuln = 2.0f;
    }

    std::set<ge::GameObject*> grounded_others_;
};

class Hud : public ge::Component {
public:
    void OnRender(float) override {
        if (!g_atlas || !g_camera) {
            return;
        }
        const ge::Vec2 base = g_camera->position() + ge::Vec2{-560.0f, 300.0f};
        draw_digits(base, g_state.score, 6, 0.6f);
        draw_digits(base + ge::Vec2{260.0f, 0.0f}, g_state.coins, 2, 0.6f);
        draw_digits(base + ge::Vec2{420.0f, 0.0f}, std::max(g_state.lives, 0), 1, 0.6f);
    }

private:
    void draw_digits(ge::Vec2 pos, int value, int width, float scale) {
        char buf[16];
        std::snprintf(buf, sizeof(buf), "%0*d", width, std::max(value, 0));
        for (int i = 0; i < width; ++i) {
            const char* fname = digit_frame(buf[i]);
            if (const ge::UvRect* f = g_atlas->frame(fname)) {
                ge::g_renderer().draw_sprite(*g_atlas->texture(), *f,
                                             pos + ge::Vec2{static_cast<float>(i) * 20.0f * scale, 0.0f},
                                             0.0f, {20.0f * scale, 20.0f * scale},
                                             {1.0f, 1.0f, 1.0f, 1.0f}, 500, 0);
            }
        }
    }

    const char* digit_frame(char c) {
        static char buf[8];
        std::snprintf(buf, sizeof(buf), "digit_%c", c);
        return buf;
    }
};

}  // namespace

int main(int argc, char** argv) {
    SDL_SetMainReady();

    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--autotest") {
            g_autotest = true;
            GE_LOG_INFO("AUTOTEST mode enabled");
        }
    }

    if (char* base = SDL_GetBasePath()) {
        std::filesystem::path root = std::filesystem::path(base).parent_path();
        for (int i = 0; i < 4; ++i) {
            if (std::filesystem::exists(root / "assets")) {
                std::filesystem::current_path(root);
                break;
            }
            root = root.parent_path();
        }
        SDL_free(base);
    }

    std::filesystem::create_directories("logs");
    ge::Logger::instance().open_file("logs/engine.log");
    GE_LOG_INFO("Super Engine Bros starting");

    ge::Window window;
    ge::Window::Config config;
    if (!window.init(config)) {
        GE_LOG_ERROR("Failed to init window");
        return 1;
    }

    if (!gladLoadGLLoader((GLADloadproc)SDL_GL_GetProcAddress)) {
        GE_LOG_ERROR("gladLoadGLLoader failed");
        return 1;
    }
    GE_LOG_INFO("OpenGL version: %s", glGetString(GL_VERSION));

    ge::InputManager input;
    ge::bind_input(&input);
    ge::InputMap input_map;
    input_map.load_from_file("assets/input_map.txt");

    ge::Renderer2D renderer;
    if (!renderer.init(20000)) {
        GE_LOG_ERROR("Renderer2D init failed");
        return 1;
    }
    ge::bind_renderer(&renderer);

    ge::AudioManager& audio = ge::AudioManager::instance();
    if (audio.init(32)) {
        audio.load_sfx("jump", "assets/audio/jump.wav");
        audio.load_sfx("coin", "assets/audio/coin.wav");
        audio.load_sfx("stomp", "assets/audio/stomp.wav");
        audio.load_sfx("break", "assets/audio/break.wav");
        audio.load_sfx("bump", "assets/audio/bump.wav");
        audio.load_sfx("die", "assets/audio/die.wav");
        audio.load_sfx("win", "assets/audio/win.wav");
        audio.set_sfx_volume(0.8f);
        audio.set_music_volume(0.45f);
        audio.play_music("assets/audio/mario_bgm.wav", 1500.0f);
    } else {
        GE_LOG_WARN("Audio disabled");
    }

    ge::ResourceManager& resources = ge::ResourceManager::instance();
    resources.set_asset_root("assets");

    ge::Texture* atlas_tex = resources.load_texture("textures/mario_atlas.png");
    if (!atlas_tex) {
        GE_LOG_ERROR("Failed to load mario atlas");
        return 1;
    }
    static ge::TextureAtlas atlas(atlas_tex);
    const auto reg = [&](const char* name, int x, int y, int w, int h) {
        atlas.add_frame_pixels(name, x, y, w, h);
    };
    const int C = 16;
    reg("mario_idle", 0, 0, C, C);
    reg("mario_run1", 0, 1 * C, C, C);
    reg("mario_run2", 0, 2 * C, C, C);
    reg("mario_jump", 0, 3 * C, C, C);
    reg("goomba_1", 1 * C, 0, C, C);
    reg("goomba_2", 1 * C, 1 * C, C, C);
    reg("koopa_1", 1 * C, 2 * C, C, C);
    reg("koopa_2", 1 * C, 3 * C, C, C);
    reg("brick", 2 * C, 0, C, C);
    reg("question", 2 * C, 1 * C, C, C);
    reg("block_used", 2 * C, 2 * C, C, C);
    reg("ground_tile", 2 * C, 3 * C, C, C);
    reg("pipe_top", 3 * C, 0, C, C);
    reg("pipe_body", 3 * C, 1 * C, C, C);
    reg("coin_1", 3 * C, 2 * C, C, C);
    reg("coin_2", 3 * C, 3 * C, C, C);
    reg("flag_top", 3 * C, 4 * C, C, C);
    reg("flag_body", 4 * C, 0, C, C);
    reg("cloud", 1 * C, 4 * C, C, C);
    reg("bush", 2 * C, 4 * C, C, C);
    reg("debris", 0 * C + 4, 4 * C + 5, 8, 8);
    const int D = 8;
    reg("digit_0", 4 * C, 1 * C, D, D);
    reg("digit_1", 4 * C + 8, 1 * C, D, D);
    reg("digit_2", 4 * C, 1 * C + 8, D, D);
    reg("digit_3", 4 * C + 8, 1 * C + 8, D, D);
    reg("digit_4", 4 * C, 2 * C, D, D);
    reg("digit_5", 4 * C + 8, 2 * C, D, D);
    reg("digit_6", 4 * C, 2 * C + 8, D, D);
    reg("digit_7", 4 * C + 8, 2 * C + 8, D, D);
    reg("digit_8", 5 * C, 1 * C, D, D);
    reg("digit_9", 5 * C + 8, 1 * C, D, D);
    g_atlas = &atlas;

    ge::Camera2D camera;
    g_camera = &camera;

    ge::PhysicsWorld world;
    ge::Scene scene;
    camera.set_position({400.0f, 120.0f});
    camera.set_zoom(1.0f);

    if (!ge::serializer::load_scene(scene, kLevelPath)) {
        GE_LOG_ERROR("Failed to load mario level");
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Super Engine Bros",
                                 "Failed to load assets/scenes/mario_level.json\n"
                                 "Please run the game from the game-engin folder.",
                                 window.sdl_window());
        return 1;
    }

    ge::GameObject* player = scene.FindByName("Player");
    if (!player) {
        GE_LOG_ERROR("Player not found");
        return 1;
    }
    MarioController* mario = player->AddComponent<MarioController>();
    mario->input_map = &input_map;
    mario->scene = &scene;

    for (ge::GameObject* go : scene.entities()) {
        const std::string& n = go->name();
        if (n.rfind("goomba", 0) == 0) {
            EnemyWalker* e = go->AddComponent<EnemyWalker>();
            (void)e;
        } else if (n.rfind("koopa", 0) == 0) {
            EnemyWalker* e = go->AddComponent<EnemyWalker>();
            e->is_koopa = true;
            e->speed = 40.0f;
        } else if (n.rfind("coin", 0) == 0 && n.rfind("popup", 0) != 0) {
            go->AddComponent<CoinPickup>();
        } else if (n.rfind("brick", 0) == 0 || n.rfind("question", 0) == 0) {
            BlockController* b = go->AddComponent<BlockController>();
            b->scene = &scene;
        }
    }
    scene.CreateEntity("hud")->AddComponent<Hud>();

    ge::TickTimer timer;
    double fps_acc = 0.0;
    double stats_acc = 0.0;
    double win_t = 0.0;
    int fps_frames = 0;
    float acc = 0.0f;

#ifdef GE_BUILD_EDITOR
    ge::EditorApp& editor = ge::EditorApp::instance();
    if (!editor.init(window.sdl_window(), window.sdl_gl_context())) {
        GE_LOG_ERROR("Editor init failed");
        return 1;
    }
#endif

    while (!window.should_close()) {
        window.poll_events();
        input.update(window.frame_events());
        const double dt = timer.tick();

#ifdef GE_BUILD_EDITOR
        editor.process_events(window.frame_events());
        const bool playing = editor.simulation_playing();
#else
        const bool playing = true;
#endif

        if (input_map.is_pressed("quit")) {
            window.request_close();
        }

        fps_acc += dt;
        stats_acc += dt;
        ++fps_frames;
        if (fps_acc >= 0.5) {
            const double fps = fps_frames / fps_acc;
            char title[128];
            std::snprintf(title, sizeof(title), "Super Engine Bros - %.1f FPS", fps);
            window.set_title(title);
            fps_acc = 0.0;
            fps_frames = 0;
        }

        if (playing) {
            if (g_state.game_over) {
                GE_LOG_INFO("Reloading level after game over (score=%d)", g_state.score);
                g_state.game_over = false;
                g_state.lives = 3;
                g_state.coins = 0;
                ge::serializer::load_scene(scene, kLevelPath);
                player = scene.FindByName("Player");
                if (player) {
                    mario = player->AddComponent<MarioController>();
                    mario->input_map = &input_map;
                    mario->scene = &scene;
                }
                for (ge::GameObject* go : scene.entities()) {
                    const std::string& n = go->name();
                    if (n.rfind("goomba", 0) == 0) {
                        go->AddComponent<EnemyWalker>();
                    } else if (n.rfind("koopa", 0) == 0) {
                        EnemyWalker* e = go->AddComponent<EnemyWalker>();
                        e->is_koopa = true;
                        e->speed = 40.0f;
                    } else if (n.rfind("coin", 0) == 0) {
                        go->AddComponent<CoinPickup>();
                    } else if (n.rfind("brick", 0) == 0 || n.rfind("question", 0) == 0) {
                        BlockController* b = go->AddComponent<BlockController>();
                        b->scene = &scene;
                    }
                }
                scene.CreateEntity("hud")->AddComponent<Hud>();
#ifdef GE_BUILD_EDITOR
                editor.clear_selection();
#endif
            }
            if (g_state.won) {
                win_t += dt;
                if (win_t > 3.0f) {
                    GE_LOG_INFO("Restarting level (score=%d)", g_state.score);
                    g_state.won = false;
                    win_t = 0.0f;
                    ge::serializer::load_scene(scene, kLevelPath);
                    player = scene.FindByName("Player");
                    if (player) {
                        mario = player->AddComponent<MarioController>();
                        mario->input_map = &input_map;
                        mario->scene = &scene;
                    }
                    for (ge::GameObject* go : scene.entities()) {
                        const std::string& n = go->name();
                        if (n.rfind("goomba", 0) == 0) {
                            go->AddComponent<EnemyWalker>();
                        } else if (n.rfind("koopa", 0) == 0) {
                            EnemyWalker* e = go->AddComponent<EnemyWalker>();
                            e->is_koopa = true;
                            e->speed = 40.0f;
                        } else if (n.rfind("coin", 0) == 0) {
                            go->AddComponent<CoinPickup>();
                        } else if (n.rfind("brick", 0) == 0 || n.rfind("question", 0) == 0) {
                            BlockController* b = go->AddComponent<BlockController>();
                            b->scene = &scene;
                        }
                    }
                    scene.CreateEntity("hud")->AddComponent<Hud>();
#ifdef GE_BUILD_EDITOR
                    editor.clear_selection();
#endif
                }
            }
            acc += std::min(static_cast<float>(dt), kMaxDt);
            while (acc >= kFixedDt) {
                scene.Update(kFixedDt);
                world.step(scene, kFixedDt);
                acc -= kFixedDt;
            }
        }
#ifdef GE_BUILD_EDITOR
        if (editor.consume_step_request()) {
            scene.Update(kFixedDt);
            world.step(scene, kFixedDt);
        }
#endif
        const float alpha = acc / kFixedDt;

        if (playing && player && mario && mario->alive) {
            const float target_x = std::clamp(player->transform.pos.x, 0.0f, 4000.0f);
            const float lerp = 1.0f - std::exp(-static_cast<float>(dt) * 8.0f);
            const ge::Vec2 cam = camera.position() +
                                 (ge::Vec2{target_x, 120.0f} - camera.position()) * lerp;
            camera.set_position(cam);
        }

#ifdef GE_BUILD_EDITOR
        int vp_w = 0;
        int vp_h = 0;
        editor.viewport_size(vp_w, vp_h);
        editor.begin_viewport(vp_w, vp_h);
        const ge::Mat4 view_proj = camera.view_proj(
            static_cast<float>(vp_w), static_cast<float>(vp_h));
        renderer.begin_frame(view_proj);
        scene.Render(alpha);
        renderer.end_frame();
        editor.end_viewport();

        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glViewport(0, 0, window.width(), window.height());
        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        editor.draw(scene, camera, static_cast<float>(timer.fps()), renderer.quad_count(),
                    renderer.draw_calls());
        ImGui::Render();
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
#else
        glViewport(0, 0, window.width(), window.height());
        glClearColor(0.5f, 0.75f, 1.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        const ge::Mat4 view_proj = camera.view_proj(
            static_cast<float>(window.width()), static_cast<float>(window.height()));
        renderer.begin_frame(view_proj);
        scene.Render(alpha);
        renderer.end_frame();
#endif

        if (stats_acc >= 2.0) {
            const ge::PhysicsWorld::Stats& s = world.stats();
            float px = player ? player->transform.pos.x : 0.0f;
            GE_LOG_INFO("bodies=%zu contacts=%zu player_x=%.0f score=%d lives=%d fps=%.1f",
                        s.bodies, s.contacts, px, g_state.score, g_state.lives, 1.0 / dt);
            stats_acc = 0.0;
        }

        window.swap();
    }

    window.shutdown();
    GE_LOG_INFO("Super Engine Bros exited");
    return 0;
}
