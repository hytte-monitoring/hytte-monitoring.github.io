cmake_minimum_required(VERSION 3.20)
project(door CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(home STATIC
    src/door.cpp
)
target_include_directories(home PUBLIC include)
if(MSVC)
    target_compile_options(home PRIVATE /W4)
else()
    target_compile_options(home PRIVATE -Wall -Wextra)
endif()

add_executable(demo src/demo.cpp)
target_link_libraries(demo PRIVATE home)
