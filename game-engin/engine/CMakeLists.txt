add_library(engine STATIC
    audio/audio_manager.cpp
    core/logger.cpp
    ecs/gameobject.cpp
    ecs/scene.cpp
    input/input_manager.cpp
    input/input_map.cpp
    physics/physics_world.cpp
    platform/window.cpp
    render/renderer2d.cpp
    render/shader.cpp
    render/stb_image.cpp
    render/texture.cpp
    resource/resource_manager.cpp
    scene/prefab.cpp
    scene/serializer.cpp
)

target_include_directories(engine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_include_directories(engine PUBLIC ${CMAKE_SOURCE_DIR}/third_party/stb)
target_include_directories(engine PUBLIC ${CMAKE_SOURCE_DIR}/third_party/json/include)
target_link_libraries(engine PUBLIC SDL2::SDL2 SDL2_mixer glad)

option(GE_BUILD_EDITOR "Build the ImGui editor layer" ON)
if(GE_BUILD_EDITOR)
    target_sources(engine PRIVATE editor/editor_app.cpp)
    target_link_libraries(engine PUBLIC imgui)
    target_compile_definitions(engine PUBLIC GE_BUILD_EDITOR=1)
endif()
