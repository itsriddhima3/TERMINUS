cmake_minimum_required(VERSION 3.20)
project(velox_probe_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY /app/bin)

add_executable(velox_probe
  src/main.cpp
  src/files.cpp
  flow/lane.cpp
  numeric/math.cpp
  numeric/reduce.cpp
  arena/body.cpp
  script/host.cpp
  text/token.cpp
  inspect/audit.cpp
  decoy/trace.cpp
  decoy/cache.cpp
  src/report.cpp
  src/config.cpp
)

target_include_directories(velox_probe PRIVATE include)
target_compile_options(velox_probe PRIVATE -Wall -Wextra -Wpedantic)
