add_executable(sandbox main.cpp)
target_link_libraries(sandbox PRIVATE engine)

add_executable(physics_test physics_test.cpp)
target_link_libraries(physics_test PRIVATE engine)

if(WIN32)
    add_custom_command(TARGET sandbox POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
                $<TARGET_FILE:SDL2::SDL2>
                $<TARGET_FILE_DIR:sandbox>)
endif()

if(MINGW)
    get_filename_component(_mingw_bin "${CMAKE_CXX_COMPILER}" DIRECTORY)
    foreach(_dll libstdc++-6.dll libgcc_s_seh-1.dll libwinpthread-1.dll)
        if(EXISTS "${_mingw_bin}/${_dll}")
            add_custom_command(TARGET sandbox POST_BUILD
                COMMAND ${CMAKE_COMMAND} -E copy_if_different
                        "${_mingw_bin}/${_dll}" $<TARGET_FILE_DIR:sandbox>)
        endif()
    endforeach()
endif()
