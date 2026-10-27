cmake_minimum_required(VERSION 3.20)
project(thermostat CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(climate STATIC
    src/heater.cpp
    src/sensor.cpp
    src/thermostat.cpp
)
target_include_directories(climate PUBLIC include)
if(MSVC)
    target_compile_options(climate PRIVATE /W4)
else()
    target_compile_options(climate PRIVATE -Wall -Wextra)
endif()

add_executable(demo src/demo.cpp)
target_link_libraries(demo PRIVATE climate)

# One executable per sequence diagram: scenarios/<scenario>.cpp for sequence-<scenario>.drawio.
add_executable(scenario_set_target scenarios/set_target.cpp)
target_link_libraries(scenario_set_target PRIVATE climate)
