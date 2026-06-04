cmake_minimum_required(VERSION 3.16)
project(arcctl CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(LibXml2 REQUIRED)
find_package(CURL REQUIRED)

add_executable(arcctl
  src/main.cpp
  src/app/batch_util.cpp
  src/app/parse_cmd.cpp
  src/app/parse_stage.cpp
  src/app/parse_load.cpp
  src/app/parse_write.cpp
  src/app/link_cmd.cpp
  src/app/link_stage.cpp
  src/app/link_names.cpp
  src/app/link_places.cpp
  src/app/report_cmd.cpp
  src/app/report_stage.cpp
  src/ingest/op_scan_x.cpp
  src/ingest/op_date_y.cpp
  src/ingest/op_emit_z.cpp
  src/net/http_client.cpp
  src/net/op_query_a.cpp
  src/net/op_resolve.cpp
  src/link/op_strip_b.cpp
  src/link/op_pick_c.cpp
  src/policy/op_acc_d.cpp
  src/policy/op_prec_e.cpp
  src/report/op_queue_f.cpp
  ../decoy/XmlStub.cpp
  ../decoy/PolicyStub.cpp
  ../decoy/DateFold.cpp
  ../decoy/SubjectStub.cpp
  ../decoy/TierStub.cpp
  ../decoy/LinkStub.cpp
)

target_include_directories(arcctl PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/include
  ${CMAKE_CURRENT_SOURCE_DIR}/vendor
)

target_link_libraries(arcctl PRIVATE LibXml2::LibXml2 CURL::libcurl)
