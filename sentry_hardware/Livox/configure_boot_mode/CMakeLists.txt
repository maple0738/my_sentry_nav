cmake_minimum_required(VERSION 3.10)
project(configure_boot_mode)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(${PROJECT_NAME} main.cpp)

target_link_libraries(${PROJECT_NAME}
  PUBLIC
  livox_lidar_sdk_shared
)