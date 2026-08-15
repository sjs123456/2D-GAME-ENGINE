add_library(imgui STATIC
    imgui.cpp
    imgui_draw.cpp
    imgui_tables.cpp
    imgui_widgets.cpp
    imgui_stdlib.cpp
    ImGuizmo.cpp
    backends/imgui_impl_opengl3.cpp
    backends/imgui_impl_sdl2.cpp
)

target_include_directories(imgui PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_include_directories(imgui PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/backends)
target_link_libraries(imgui PUBLIC SDL2::SDL2)
