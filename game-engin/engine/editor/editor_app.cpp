#include "editor/editor_app.h"

#include <filesystem>
#include <random>

#include <glad/glad.h>
#include <imgui.h>
#include <imgui_impl_opengl3.h>
#include <imgui_impl_sdl2.h>
#include <imgui_stdlib.h>
#include <ImGuizmo.h>

#include "audio/audio_source.h"
#include "core/logger.h"
#include "ecs/component.h"
#include "ecs/gameobject.h"
#include "physics/collider.h"
#include "physics/rigidbody.h"
#include "render/sprite_renderer.h"
#include "resource/resource_manager.h"
#include "scene/prefab.h"
#include "scene/serializer.h"

namespace ge {

namespace {
EditorApp* s_editor = nullptr;

bool is_point_in_quad(Vec2 point, const Transform& t) {
    const Vec2 half = t.scale * 0.5f;
    return point.x >= t.pos.x - half.x && point.x <= t.pos.x + half.x &&
           point.y >= t.pos.y - half.y && point.y <= t.pos.y + half.y;
}
}  // namespace

EditorApp::~EditorApp() {
    shutdown();
}

EditorApp& EditorApp::instance() {
    static EditorApp editor;
    return editor;
}

bool EditorApp::enabled() {
    return s_editor != nullptr;
}

bool EditorApp::init(SDL_Window* window, SDL_GLContext context) {
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_DockingEnable;
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    io.IniFilename = "imgui.ini";

    ImGui::StyleColorsDark();

    if (!ImGui_ImplSDL2_InitForOpenGL(window, context)) {
        GE_LOG_ERROR("Editor: ImGui_ImplSDL2 init failed");
        return false;
    }
    if (!ImGui_ImplOpenGL3_Init("#version 330")) {
        GE_LOG_ERROR("Editor: ImGui_ImplOpenGL3 init failed");
        return false;
    }

    glGenFramebuffers(1, &fbo_);
    glGenTextures(1, &fbo_texture_);
    glGenRenderbuffers(1, &fbo_depth_);

    Logger::instance().set_sink([this](LogLevel level, const std::string& message) {
        console_lines_.push_back({level, message});
        if (console_lines_.size() > 200) {
            console_lines_.pop_front();
        }
    });

    s_editor = this;
    GE_LOG_INFO("Editor initialized");
    return true;
}

void EditorApp::shutdown() {
    if (s_editor != this) {
        return;
    }
    if (fbo_) {
        glDeleteFramebuffers(1, &fbo_);
        glDeleteTextures(1, &fbo_texture_);
        glDeleteRenderbuffers(1, &fbo_depth_);
        fbo_ = fbo_texture_ = fbo_depth_ = 0;
    }
    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplSDL2_Shutdown();
    ImGui::DestroyContext();
    s_editor = nullptr;
}

void EditorApp::process_events(const std::vector<SDL_Event>& events) {
    for (const SDL_Event& e : events) {
        ImGui_ImplSDL2_ProcessEvent(&e);
    }
}

void EditorApp::begin_viewport(int fb_width, int fb_height) {
    if (fbo_width_ != fb_width || fbo_height_ != fb_height) {
        glBindTexture(GL_TEXTURE_2D, fbo_texture_);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, fb_width, fb_height, 0, GL_RGBA,
                     GL_UNSIGNED_BYTE, nullptr);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glBindRenderbuffer(GL_RENDERBUFFER, fbo_depth_);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, fb_width, fb_height);
        glBindFramebuffer(GL_FRAMEBUFFER, fbo_);
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D,
                               fbo_texture_, 0);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER,
                                  fbo_depth_);
        fbo_width_ = fb_width;
        fbo_height_ = fb_height;
    }
    glBindFramebuffer(GL_FRAMEBUFFER, fbo_);
    glViewport(0, 0, fb_width, fb_height);
    glClearColor(0.08f, 0.09f, 0.12f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}

void EditorApp::end_viewport() {
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
}

GameObject* EditorApp::pick_entity(const Scene& scene, Vec2 world) const {
    GameObject* best = nullptr;
    int best_order = -1;
    for (GameObject* go : scene.entities()) {
        if (!go->active()) {
            continue;
        }
        const SpriteRenderer* spr = go->GetComponent<SpriteRenderer>();
        if (!spr) {
            continue;
        }
        if (!is_point_in_quad(world, go->transform)) {
            continue;
        }
        const int order = spr->layer * 1000 + spr->sort_order;
        if (order >= best_order) {
            best_order = order;
            best = go;
        }
    }
    return best;
}

void EditorApp::draw(Scene& scene, Camera2D& camera, float fps, unsigned int sprites,
                     unsigned int draw_calls) {
    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplSDL2_NewFrame();
    ImGui::NewFrame();
    ImGuizmo::BeginFrame();

    const ImGuiViewport* viewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(viewport->Pos);
    ImGui::SetNextWindowSize(viewport->Size);
    ImGui::SetNextWindowViewport(viewport->ID);
    ImGuiWindowFlags host_flags = ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoCollapse |
                                  ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoMove |
                                  ImGuiWindowFlags_NoBringToFrontOnFocus |
                                  ImGuiWindowFlags_NoNavFocus | ImGuiWindowFlags_NoBackground |
                                  ImGuiWindowFlags_NoDocking;
    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 0.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize, 0.0f);
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0.0f, 0.0f));
    ImGui::Begin("DockSpace", nullptr, host_flags);
    ImGui::PopStyleVar(3);
    ImGui::DockSpace(ImGui::GetID("EditorDockSpace"));
    ImGui::End();

    draw_toolbar(scene, fps, sprites, draw_calls);
    draw_hierarchy(scene);
    draw_inspector(scene, camera);
    draw_assets(scene);
    draw_console();
    draw_viewport(scene, camera);
}

void EditorApp::draw_toolbar(Scene& scene, float fps, unsigned int sprites,
                             unsigned int draw_calls) {
    ImGui::Begin("Toolbar");
    if (ImGui::Button(playing_ ? "Pause" : "Play")) {
        playing_ = !playing_;
    }
    ImGui::SameLine();
    if (ImGui::Button("Step") && !playing_) {
        pending_step_ = true;
    }
    ImGui::SameLine();
    if (ImGui::Button("Save Scene")) {
        serializer::save_scene(scene, "assets/scenes/editor_scene.json");
    }
    ImGui::SameLine();
    if (ImGui::Button("Load Scene")) {
        serializer::load_scene(scene, "assets/scenes/editor_scene.json");
        selected_ = nullptr;
    }
    ImGui::Text("fps=%.0f sprites=%u draws=%u", fps, sprites, draw_calls);
    ImGui::End();
}

void EditorApp::draw_hierarchy(Scene& scene) {
    ImGui::Begin("Hierarchy");
    if (ImGui::Button("New Entity")) {
        char name[32];
        std::snprintf(name, sizeof(name), "entity_%d", instantiate_counter_++);
        selected_ = scene.CreateEntity(name);
        renaming_ = true;
        rename_buffer_ = selected_->name();
    }
    ImGui::SameLine();
    if (ImGui::Button("Delete Selected") && selected_) {
        scene.DestroyEntity(selected_);
        selected_ = nullptr;
    }
    ImGui::Separator();

    if (ImGui::TreeNodeEx("Scene", ImGuiTreeNodeFlags_DefaultOpen)) {
        for (GameObject* go : scene.entities()) {
            const bool is_selected = go == selected_;
            ImGuiTreeNodeFlags flags = ImGuiTreeNodeFlags_Leaf;
            if (is_selected) {
                flags |= ImGuiTreeNodeFlags_Selected;
            }
            ImGui::PushID(go);
            if (ImGui::TreeNodeEx("##node", flags, "%s", go->name().c_str())) {
                if (ImGui::IsItemClicked()) {
                    selected_ = go;
                    renaming_ = false;
                }
                if (ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(0)) {
                    renaming_ = true;
                    rename_buffer_ = go->name();
                }
                if (renaming_ && go == selected_) {
                    ImGui::SetNextItemWidth(160.0f);
                    if (ImGui::InputText("##rename", &rename_buffer_,
                                         ImGuiInputTextFlags_EnterReturnsTrue)) {
                        go->set_name(rename_buffer_);
                        renaming_ = false;
                    }
                }
                ImGui::TreePop();
            }
            ImGui::PopID();
        }
        ImGui::TreePop();
    }
    ImGui::End();
}

void EditorApp::draw_inspector(Scene&, Camera2D& camera) {
    ImGui::Begin("Inspector");
    if (!selected_) {
        ImGui::Text("No entity selected");
        ImGui::Separator();
        ImGui::Text("Camera");
        float pos[2] = {camera.position().x, camera.position().y};
        if (ImGui::DragFloat2("position", pos, 5.0f)) {
            camera.set_position({pos[0], pos[1]});
        }
        float zoom = camera.zoom();
        if (ImGui::DragFloat("zoom", &zoom, 0.01f, 0.05f, 20.0f)) {
            camera.set_zoom(zoom);
        }
        ImGui::End();
        return;
    }

    GameObject& go = *selected_;
    ImGui::Text("Entity: %s", go.name().c_str());

    Transform& t = go.transform;
    float pos[2] = {t.pos.x, t.pos.y};
    if (ImGui::DragFloat2("pos", pos, 1.0f)) {
        t.pos = {pos[0], pos[1]};
    }
    if (ImGui::DragFloat("rot", &t.rot, 0.01f)) {
    }
    float scale[2] = {t.scale.x, t.scale.y};
    if (ImGui::DragFloat2("scale", scale, 1.0f, 0.1f, 100000.0f)) {
        t.scale = {scale[0], scale[1]};
    }
    bool active = go.active();
    if (ImGui::Checkbox("active", &active)) {
        go.set_active(active);
    }
    ImGui::Separator();

    for (Component* c : go.components()) {
        ImGui::PushID(c);
        const char* type_name =
            dynamic_cast<SpriteRenderer*>(c) ? "SpriteRenderer" :
            dynamic_cast<RigidBody*>(c) ? "RigidBody" :
            dynamic_cast<CircleCollider*>(c) ? "CircleCollider" :
            dynamic_cast<BoxCollider*>(c) ? "BoxCollider" :
            dynamic_cast<AudioSource*>(c) ? "AudioSource" : "Unknown";
        bool open = ImGui::CollapsingHeader(type_name, ImGuiTreeNodeFlags_DefaultOpen);
        if (open) {
            if (auto* spr = dynamic_cast<SpriteRenderer*>(c)) {
                float color[4] = {spr->color.r, spr->color.g, spr->color.b, spr->color.a};
                if (ImGui::ColorEdit4("color", color)) {
                    spr->color = {color[0], color[1], color[2], color[3]};
                }
                ImGui::DragInt("layer", &spr->layer, 1.0f);
                ImGui::DragInt("sortOrder", &spr->sort_order, 1.0f);
                ImGui::Checkbox("interpolate", &spr->interpolate);
            } else if (auto* rb = dynamic_cast<RigidBody*>(c)) {
                float v[2] = {rb->velocity.x, rb->velocity.y};
                if (ImGui::DragFloat2("velocity", v, 1.0f)) {
                    rb->velocity = {v[0], v[1]};
                }
                ImGui::DragFloat("gravityScale", &rb->gravity_scale, 0.01f, 0.0f, 10.0f);
                ImGui::DragFloat("restitution", &rb->restitution, 0.01f, 0.0f, 1.0f);
                ImGui::DragFloat("mass", &rb->mass, 0.1f, 0.01f, 1000.0f);
                ImGui::Checkbox("isStatic", &rb->is_static);
            } else if (auto* col = dynamic_cast<CircleCollider*>(c)) {
                ImGui::DragFloat("radius", &col->radius, 0.5f, 0.1f, 100000.0f);
                float off[2] = {col->offset.x, col->offset.y};
                if (ImGui::DragFloat2("offset", off, 1.0f)) {
                    col->offset = {off[0], off[1]};
                }
            } else if (auto* col = dynamic_cast<BoxCollider*>(c)) {
                float size[2] = {col->size.x, col->size.y};
                if (ImGui::DragFloat2("size", size, 1.0f, 0.1f, 100000.0f)) {
                    col->size = {size[0], size[1]};
                }
                float off[2] = {col->offset.x, col->offset.y};
                if (ImGui::DragFloat2("offset", off, 1.0f)) {
                    col->offset = {off[0], off[1]};
                }
            } else if (auto* src = dynamic_cast<AudioSource*>(c)) {
                char buf[64];
                std::snprintf(buf, sizeof(buf), "%s", src->sound.c_str());
                if (ImGui::InputText("sound", buf, sizeof(buf))) {
                    src->sound = buf;
                }
                ImGui::Checkbox("playOnCollision", &src->play_on_collision);
                ImGui::DragFloat("volume", &src->volume, 0.01f, 0.0f, 1.0f);
                ImGui::DragFloat("range", &src->range, 10.0f, 1.0f, 100000.0f);
            }
            if (ImGui::Button("Remove")) {
                go.RemoveComponent(c);
                ImGui::PopID();
                break;
            }
        }
        ImGui::PopID();
    }

    ImGui::Separator();
    ImGui::Text("Add component");
    ImGui::SameLine();
    const char* types[] = {"SpriteRenderer", "RigidBody", "CircleCollider",
                           "BoxCollider", "AudioSource"};
    ImGui::SetNextItemWidth(140.0f);
    ImGui::Combo("##add_type", &add_component_type_, types, 5);
    ImGui::SameLine();
    if (ImGui::Button("Add")) {
        switch (add_component_type_) {
            case 0: go.AddComponent<SpriteRenderer>(); break;
            case 1: go.AddComponent<RigidBody>(); break;
            case 2: go.AddComponent<CircleCollider>(); break;
            case 3: go.AddComponent<BoxCollider>(); break;
            case 4: go.AddComponent<AudioSource>(); break;
            default: break;
        }
    }
    ImGui::End();
}

void EditorApp::draw_assets(Scene& scene) {
    ImGui::Begin("Assets");
    if (ImGui::CollapsingHeader("Prefabs", ImGuiTreeNodeFlags_DefaultOpen)) {
        prefab_files_.clear();
        std::error_code ec;
        for (const auto& entry : std::filesystem::directory_iterator("assets/prefabs", ec)) {
            if (entry.path().extension() == ".json") {
                prefab_files_.push_back(entry.path().filename().string());
            }
        }
        for (const std::string& file : prefab_files_) {
            ImGui::PushID(file.c_str());
            if (ImGui::Button(file.c_str())) {
                char id[48];
                std::snprintf(id, sizeof(id), "prefab_%d", instantiate_counter_++);
                prefab::instantiate("assets/prefabs/" + file, scene, id);
            }
            ImGui::PopID();
        }
    }
    if (ImGui::CollapsingHeader("Textures", ImGuiTreeNodeFlags_DefaultOpen)) {
        texture_files_.clear();
        std::error_code ec;
        for (const auto& entry : std::filesystem::directory_iterator("assets/textures", ec)) {
            if (entry.path().extension() == ".png") {
                texture_files_.push_back(entry.path().filename().string());
            }
        }
        for (const std::string& file : texture_files_) {
            ImGui::PushID(file.c_str());
            if (ImGui::Button(file.c_str())) {
                char name[48];
                std::snprintf(name, sizeof(name), "sprite_%d", spawn_counter_++);
                GameObject* obj = scene.CreateEntity(name);
                obj->transform.pos = {static_cast<float>(spawn_counter_ * 40 - 400), 0.0f};
                SpriteRenderer* spr = obj->AddComponent<SpriteRenderer>();
                spr->texture = ResourceManager::instance().load_texture("textures/" + file);
                if (spr->texture) {
                    obj->transform.scale = {static_cast<float>(spr->texture->width()),
                                            static_cast<float>(spr->texture->height())};
                }
                selected_ = obj;
            }
            ImGui::PopID();
        }
    }
    ImGui::End();
}

void EditorApp::draw_console() {
    ImGui::Begin("Console");
    for (const auto& [level, message] : console_lines_) {
        const ImVec4 color =
            level == LogLevel::Error ? ImVec4(1.0f, 0.4f, 0.4f, 1.0f) :
            level == LogLevel::Warn  ? ImVec4(1.0f, 0.85f, 0.4f, 1.0f) :
            level == LogLevel::Debug ? ImVec4(0.6f, 0.6f, 0.6f, 1.0f) :
                                       ImVec4(0.8f, 0.9f, 1.0f, 1.0f);
        ImGui::TextColored(color, "%s", message.c_str());
    }
    ImGui::End();
}

void EditorApp::draw_viewport(Scene& scene, Camera2D& camera) {
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0.0f, 0.0f));
    ImGui::Begin("Viewport");
    const ImVec2 size = ImGui::GetContentRegionAvail();
    last_vp_width_ = static_cast<int>(size.x);
    last_vp_height_ = static_cast<int>(size.y);
    const bool hovered = ImGui::IsWindowHovered();

    ImGui::Image(static_cast<ImTextureID>(static_cast<intptr_t>(fbo_texture_)), size,
                 ImVec2(0.0f, 1.0f), ImVec2(1.0f, 0.0f));

    const ImVec2 vp_size = ImGui::GetWindowSize();
    const ImVec2 vp_pos = ImGui::GetWindowContentRegionMin();

    if (hovered) {
        const ImVec2 mouse = ImGui::GetIO().MousePos;
        const Vec2 screen = {mouse.x - vp_pos.x, mouse.y - vp_pos.y};
        const Vec2 world = camera.screen_to_world(screen, vp_size.x, vp_size.y);

        if (ImGui::IsMouseClicked(0) && !ImGuizmo::IsOver()) {
            selected_ = pick_entity(scene, world);
            renaming_ = false;
        }
        if (ImGui::IsMouseDragging(1) || ImGui::IsMouseDragging(2)) {
            const ImVec2 delta = ImGui::GetIO().MouseDelta;
            camera.set_position(camera.position() - Vec2{delta.x, delta.y} / camera.zoom());
        }
        if (ImGui::GetIO().MouseWheel != 0.0f) {
            camera.set_zoom(camera.zoom() * (ImGui::GetIO().MouseWheel > 0.0f ? 1.1f : 0.9f));
        }
    }

    if (selected_) {
        const float vp_w = vp_size.x;
        const float vp_h = vp_size.y;
        const Mat4 view = Mat4::identity();
        const Mat4 proj = camera.view_proj(vp_w, vp_h);

        ImGuizmo::SetRect(vp_pos.x, vp_pos.y, vp_w, vp_h);
        Mat4 model = Mat4::translation(selected_->transform.pos.x, selected_->transform.pos.y);
        Mat4 delta;
        if (ImGuizmo::Manipulate(view.m, proj.m, ImGuizmo::TRANSLATE, ImGuizmo::WORLD,
                                 model.m, delta.m)) {
            selected_->transform.pos = {model.m[12], model.m[13]};
        }
    }

    ImGui::End();
    ImGui::PopStyleVar();
}

}  // namespace ge
