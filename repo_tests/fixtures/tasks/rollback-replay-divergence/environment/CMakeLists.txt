cmake_minimum_required(VERSION 3.25)
project(netplay_lab LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT DEFINED TB_TIMELINE_MODE)
  set(TB_TIMELINE_MODE 1)
endif()
if(NOT DEFINED TB_REEXEC_MODE)
  set(TB_REEXEC_MODE 1)
endif()

add_executable(netplay_matrix
  src/main.cpp
  src/game/world.cpp
  src/game/components.cpp
  src/net/transport.cpp
  src/net/session.cpp
  src/net/prediction.cpp
  src/sim/tick_driver.cpp
  src/sim/snapshot.cpp
  src/sim/input_merge.cpp
  src/sim/command_log.cpp
  src/sim/rng_facade.cpp
  src/replay/encoder.cpp
  src/replay/decoder.cpp
  src/replay/version.cpp
  src/replay/io.cpp
  src/replay/resume.cpp
  src/harness/runner.cpp
  src/harness/trace.cpp
  src/util/checksum.cpp
  src/util/logging.cpp
  src/util/buffer.cpp
  src/util/json_scan.cpp
)

target_include_directories(netplay_matrix PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_definitions(netplay_matrix PRIVATE
  TB_TIMELINE_MODE=${TB_TIMELINE_MODE}
  TB_REEXEC_MODE=${TB_REEXEC_MODE}
)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(netplay_matrix PRIVATE -Wall -Wextra -Wpedantic)
endif()

install(TARGETS netplay_matrix RUNTIME DESTINATION bin)
