cmake_minimum_required(VERSION 3.16)
project(ratectl CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(CURL REQUIRED)

add_library(http_util lib/http_util.cpp)
target_link_libraries(http_util PUBLIC CURL::libcurl)

add_library(decoy decoy/q2n/page.cpp decoy/n8f/codec.cpp)

add_executable(ratectl
  cmd/ratectl/main.cpp
  cmd/ratectl/run_fetch.cpp
  cmd/ratectl/run_train.cpp
  cmd/ratectl/run_submit.cpp
  client/k3p/pull.cpp
  core/r7n/loop.cpp
  core/m4t/pack.cpp
  core/p1v/submit.cpp
)
target_include_directories(ratectl PRIVATE ${CMAKE_SOURCE_DIR})
target_link_libraries(ratectl PRIVATE http_util decoy CURL::libcurl)

install(TARGETS ratectl RUNTIME DESTINATION bin)
