cmake_minimum_required(VERSION 3.14)
project(pyparser LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG        v2.11.1
)
FetchContent_MakeAvailable(pybind11)

set(SOURCES
    parser.cpp
    bindings.cpp
)

pybind11_add_module(pyparser MODULE
    ${SOURCES}
)

target_include_directories(pyparser
    PRIVATE ${CMAKE_SOURCE_DIR}
)

install(TARGETS pyparser
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/lib
    ARCHIVE DESTINATION ${CMAKE_INSTALL_PREFIX}/lib
    RUNTIME DESTINATION ${CMAKE_INSTALL_PREFIX}/bin
)
