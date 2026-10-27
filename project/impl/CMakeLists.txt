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
