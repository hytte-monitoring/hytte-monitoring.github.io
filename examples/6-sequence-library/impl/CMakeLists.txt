cmake_minimum_required(VERSION 3.20)
project(lending CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(lending STATIC
    src/book.cpp
    src/catalog.cpp
    src/library.cpp
    src/loan.cpp
    src/member.cpp
)
target_include_directories(lending PUBLIC include)
if(MSVC)
    target_compile_options(lending PRIVATE /W4)
else()
    target_compile_options(lending PRIVATE -Wall -Wextra)
endif()

add_executable(demo src/demo.cpp)
target_link_libraries(demo PRIVATE lending)

# One executable per sequence diagram: scenarios/<scenario>.cpp for sequence-<scenario>.drawio.
add_executable(scenario_lend_book scenarios/lend_book.cpp)
target_link_libraries(scenario_lend_book PRIVATE lending)

add_executable(scenario_return_book scenarios/return_book.cpp)
target_link_libraries(scenario_return_book PRIVATE lending)
