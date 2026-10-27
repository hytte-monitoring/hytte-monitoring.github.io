cmake_minimum_required(VERSION 3.20)
project(library_impl CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(library STATIC
    src/book.cpp
    src/date.cpp
    src/dvd.cpp
    src/library.cpp
    src/library_item.cpp
    src/loan.cpp
    src/loan_validator.cpp
    src/member.cpp
    src/search_query.cpp
)
target_include_directories(library PUBLIC include)
if(MSVC)
    target_compile_options(library PRIVATE /W4)
else()
    target_compile_options(library PRIVATE -Wall -Wextra)
endif()

add_executable(demo src/demo.cpp)
target_link_libraries(demo PRIVATE library)
