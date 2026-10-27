cmake_minimum_required(VERSION 3.20)
project(hytte CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(hytte STATIC
    src/cabin.cpp
    src/connection_sensor.cpp
    src/door_sensor.cpp
    src/emergency_contact.cpp
    src/hytte_owner.cpp
    src/incident.cpp
    src/incident_history.cpp
    src/indoor_temperature_sensor.cpp
    src/monitoring_system.cpp
    src/motion_sensor.cpp
    src/outdoor_temperature_sensor.cpp
    src/power_sensor.cpp
    src/sensor.cpp
    src/smoke_sensor.cpp
    src/water_leak_sensor.cpp
)
target_include_directories(hytte PUBLIC include)
if(MSVC)
    target_compile_options(hytte PRIVATE /W4)
else()
    target_compile_options(hytte PRIVATE -Wall -Wextra)
endif()

add_executable(demo src/demo.cpp)
target_link_libraries(demo PRIVATE hytte)

add_executable(scenario_smoke_escalation scenarios/smoke_escalation.cpp)
target_link_libraries(scenario_smoke_escalation PRIVATE hytte)

# Unit tests (Phase 3). Run: ctest --test-dir build
enable_testing()
foreach(name test_incident test_cabin_and_sensor test_system_operation)
    add_executable(${name} tests/${name}.cpp)
    target_link_libraries(${name} PRIVATE hytte)
    add_test(NAME ${name} COMMAND ${name})
endforeach()

# Host benchmark (Phase 3). Build with -DCMAKE_BUILD_TYPE=Release for real numbers.
add_executable(benchmark benchmarks/benchmark.cpp)
target_link_libraries(benchmark PRIVATE hytte)
