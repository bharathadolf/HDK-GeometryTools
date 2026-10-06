cmake_minimum_required(VERSION 3.22)
project(Bharath_GeometryTools VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ------------------------------------------------------------------------------
# 1. Locate Houdini HDK Installation
# ------------------------------------------------------------------------------
# If HFS or HOUDINI_ROOT is set in environment or CMake args, use it.
if(DEFINED ENV{HFS} AND NOT DEFINED HOUDINI_ROOT)
    set(HOUDINI_ROOT "$ENV{HFS}")
endif()

if(NOT DEFINED HOUDINI_ROOT)
    # Default fallback check for common Windows Houdini installations
    file(GLOB HOUDINI_CANDIDATES "C:/Program Files/Side Effects Software/Houdini *")
    if(HOUDINI_CANDIDATES)
        list(REVERSE HOUDINI_CANDIDATES)
        list(GET HOUDINI_CANDIDATES 0 HOUDINI_ROOT)
        message(STATUS "Auto-detected Houdini installation at: ${HOUDINI_ROOT}")
    else()
        message(FATAL_ERROR "Could not find Houdini. Please set HOUDINI_ROOT or HFS environment variable.")
    endif()
endif()

list(APPEND CMAKE_PREFIX_PATH "${HOUDINI_ROOT}/toolkit/cmake")
find_package(Houdini REQUIRED)

# ------------------------------------------------------------------------------
# 2. Compiler & Platform Flags (Windows MSVC specifics)
# ------------------------------------------------------------------------------
if(MSVC)
    add_compile_options(
        /W3
        /permissive-
        /EHsc
        /bigobj
        /Zc:__cplusplus
    )
    add_definitions(-DNOMINMAX -D_USE_MATH_DEFINES)
endif()

# ------------------------------------------------------------------------------
# 3. Output Directory Structure for Houdini Package
# ------------------------------------------------------------------------------
set(PLUGIN_OUTPUT_DIR "${CMAKE_BINARY_DIR}/install/Bharath_GeometryTools")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${PLUGIN_OUTPUT_DIR}/dso")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${PLUGIN_OUTPUT_DIR}/dso")

# ------------------------------------------------------------------------------
# 4. Target: SOP_ScalePoints (C++ HDK Plugin)
# ------------------------------------------------------------------------------
set(SOURCE_FILES
    src/SOP_ScalePoints.h
    src/SOP_ScalePoints.C
)

add_library(SOP_ScalePoints SHARED ${SOURCE_FILES})

# Houdini library configuration helper
houdini_configure_target(SOP_ScalePoints)

target_include_directories(SOP_ScalePoints PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/src"
)

# ------------------------------------------------------------------------------
# 5. Asset & Script Deployment
# ------------------------------------------------------------------------------
# Copy scripts, help, and python files to package output
add_custom_command(TARGET SOP_ScalePoints POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "${PLUGIN_OUTPUT_DIR}/scripts/python/bharath_tools"
    COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_CURRENT_SOURCE_DIR}/scripts/python/bharath_tools" "${PLUGIN_OUTPUT_DIR}/scripts/python/bharath_tools"
    COMMAND ${CMAKE_COMMAND} -E make_directory "${PLUGIN_OUTPUT_DIR}/help/nodes/sop"
    COMMAND ${CMAKE_COMMAND} -E copy_directory "${CMAKE_CURRENT_SOURCE_DIR}/help/nodes/sop" "${PLUGIN_OUTPUT_DIR}/help/nodes/sop"
    COMMENT "Deploying Python scripts and Help files to package directory..."
)

# ------------------------------------------------------------------------------
# 6. Generate Houdini Package JSON File
# ------------------------------------------------------------------------------
set(PACKAGE_JSON_IN "${CMAKE_CURRENT_SOURCE_DIR}/package/Bharath_GeometryTools.json.in")
set(PACKAGE_JSON_OUT "${CMAKE_BINARY_DIR}/Bharath_GeometryTools.json")

configure_file(${PACKAGE_JSON_IN} ${PACKAGE_JSON_OUT} @ONLY)

message(STATUS "Configured Bharath::GeometryTools successfully for Houdini ${Houdini_VERSION}")
