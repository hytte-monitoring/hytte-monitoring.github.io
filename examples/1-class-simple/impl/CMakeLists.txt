cmake_minimum_required(VERSION 3.20)
project(playlist CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(music STATIC
    src/artist.cpp
    src/playlist.cpp
    src/song.cpp
)
target_include_directories(music PUBLIC include)
if(MSVC)
    target_compile_options(music PRIVATE /W4)
else()
    target_compile_options(music PRIVATE -Wall -Wextra)
endif()

add_executable(demo src/demo.cpp)
target_link_libraries(demo PRIVATE music)
