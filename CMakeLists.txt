#  Software License Agreement (BSD License)
#  Copyright (c) 2019-2021, AMBF.
#  (https://github.com/WPI-AIM/ambf)
#
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#  * Redistributions of source code must retain the above copyright
#  notice, this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above
#  copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials provided
#  with the distribution.
#
#  * Neither the name of authors nor the names of its contributors may
#  be used to endorse or promote products derived from this software
#  without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#
#  $Author: seb $
#  $Author: Adnan Munawar $
#  $Date:  April, 2019 $


#
# project configuration
#
# COURTESY:
# Starting point from CMakeLists of CHAI3D by SEB

cmake_minimum_required (VERSION 3.1)
project (AMBF)

# Set C++ Standard
set (CMAKE_CXX_STANDARD 11)

# set version info
file (READ ${PROJECT_SOURCE_DIR}/ambf_framework/version.txt VERSION)
STRING (REGEX REPLACE ".*MAJOR=([0-9]+).*" "\\1" MAJOR_VERSION "${VERSION}")
STRING (REGEX REPLACE ".*MINOR=([0-9]+).*" "\\1" MINOR_VERSION "${VERSION}")
STRING (REGEX REPLACE ".*RELEASE=([0-9]+).*" "\\1" RELEASE_VERSION "${VERSION}")
set (PROJECT_VERSION ${MAJOR_VERSION}.${MINOR_VERSION}.${RELEASE_VERSION})

# platform detection
if (${CMAKE_SYSTEM_NAME} MATCHES Windows)
  set (OS "win")
  if (${CMAKE_CL_64})
    set (ARCH "x64")
  else ()
    set (ARCH "Win32")
  endif ()
elseif (${CMAKE_SYSTEM_NAME} MATCHES Linux)
  set (OS "lin")
  if (${CMAKE_SIZEOF_VOID_P} EQUAL 8)
    set (ARCH "x86_64")
  else ()
    set (ARCH "i686")
  endif ()
elseif (${CMAKE_SYSTEM_NAME} MATCHES Darwin)
  set (OS "mac")
  set (ARCH "x86_64")
endif ()

# enforce build type
if (NOT CMAKE_BUILD_TYPE)
  set (CMAKE_BUILD_TYPE Release CACHE STRING "Setting build mode to Release" FORCE)
endif()

# output location
set (CMAKE_RUNTIME_OUTPUT_DIRECTORY                ${PROJECT_BINARY_DIR}/../bin/${OS}-${ARCH})
set (CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG          ${PROJECT_BINARY_DIR}/../bin-debug/${OS}-${ARCH})
set (CMAKE_RUNTIME_OUTPUT_DIRECTORY_MINSIZEREL     ${PROJECT_BINARY_DIR}/../bin/${OS}-${ARCH})
set (CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE        ${PROJECT_BINARY_DIR}/../bin/${OS}-${ARCH})
set (CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELWITHDEBINFO ${PROJECT_BINARY_DIR}/../bin/${OS}-${ARCH})

set(CHAI3D_DEFINITIONS "")
set(BULLET_DEFINITIONS "")
set(AMBF_DEFINITIONS "")
set(COMMON_DEFINITIONS "")

# SET PATHS
add_definitions(-DAMBF_ROOT_PATH="${PROJECT_SOURCE_DIR}")
add_definitions(-DAMBF_PLUGIN_PATH="${PROJECT_SOURCE_DIR}/build/ambf_plugins")

# find dependencies
find_package(OpenGL REQUIRED)
find_package(Boost COMPONENTS filesystem REQUIRED)

include_directories (${OPENGL_INCLUDE_DIR})
include_directories(${Boost_INCLUDE_DIRS})

find_package(yaml-cpp QUIET)
if (NOT yaml-cpp_FOUND)
    message(STATUS "-- *** YAML-CPP NOT FOUND, ADDING IT AS AN EXTERNAL PROJECT")
    include(cmake/ExternalYamlCpp.cmake)
endif()
include_directories(${YAML_CPP_INCLUDE_DIR})

set(AMBF_ROS_INCLUDE_DIRS "")
set(AMBF_ROS_LIBRARIES "")
# ROS Dependency
if (${CMAKE_SYSTEM_NAME} MATCHES Linux)
    find_package(catkin COMPONENTS
      roscpp
    )
    if (catkin_FOUND)
        message("-- *** FOUND ROS ON THIS MACHINE, ENABLING SUPPORT FOR AMBF_ROS MODULES")
        add_subdirectory(${PROJECT_SOURCE_DIR}/ambf_ros_modules)
        add_subdirectory(${PROJECT_SOURCE_DIR}/external/tf_function)
        # Call find catkin again, with REQUIRED this time, it's okay to write over previously
        # imported catkin variables
        find_package(catkin QUIET COMPONENTS ambf_server ambf_msgs dvrk_arm razer_hydra cv_bridge image_transport ambf_client)
              find_package(tf_function REQUIRED)

        if(ambf_server_FOUND AND ambf_msgs_FOUND AND dvrk_arm_FOUND AND ambf_client_FOUND)
            message(STATUS "-- *** FOUND AMBF_COMM, AMBF_MSGS, AMBF_CLIENT and DVRK_ARM, ENABLING DVRK DEVICE SUPPORT")

            set(AMBF_ROS_INCLUDE_DIRS ${AMBF_ROS_INCLUDE_DIRS} ${catkin_INCLUDE_DIRS})
            set(AMBF_ROS_LIBRARIES ${AMBF_ROS_LIBRARIES} ${catkin_LIBRARIES})

            list(APPEND AMBF_DEFINITIONS -DAF_ENABLE_AMBF_COMM_SUPPORT)
            list(APPEND CHAI3D_DEFINITIONS -DC_ENABLE_AMBF_DVRK_DEVICE_SUPPORT)

        else()
            message(STATUS "-- *** AMBF_COMM, AMBF_MSGS, AMBF_CLIENT and DVRK_ARM NOT FOUND")
        endif()

        find_package(OpenCV QUIET)
        if(OpenCV_FOUND)
            message(STATUS "-- *** FOUND OPENCV")
            if(cv_bridge_FOUND AND image_transport_FOUND)
                message(STATUS "-- *** FOUND ROS_CV_BRIDGE and IMAGE_TRANSPORT, ENABLING VIDEO PUBLISHING SUPPORT")

                list(APPEND AMBF_DEFINITIONS -DAF_ENABLE_OPEN_CV_SUPPORT)
                set(AMBF_ROS_INCLUDE_DIRS ${AMBF_ROS_INCLUDE_DIRS} ${OpenCV_INCLUDE_DIRS})
                set(AMBF_ROS_LIBRARIES ${AMBF_ROS_LIBRARIES} ${OpenCV_LIBRARIES})
            else()
                message(STATUS "-- *** ROS CV_BRIDGE and IMAGE_TRANSPORT NOT FOUND")
            endif()
        endif()

        if (razer_hydra_FOUND)
            message(STATUS "-- *** FOUND RAZER HYDRA'S ROS PACKAGE, ENABLING DEVICE SUPPORT")

            set(AMBF_ROS_INCLUDE_DIRS ${AMBF_ROS_INCLUDE_DIRS} ${razer_hydra_INCLUDE_DIRS})
            set(AMBF_ROS_LIBRARIES ${AMBF_ROS_LIBRARIES} ${razer_hydra_LIBRARIES})

            list(APPEND AMBF_DEFINITIONS -DC_ENABLE_RAZER_HYDRA_DEVICE_SUPPORT)
            list(APPEND CHAI3D_DEFINITIONS -DC_ENABLE_RAZER_HYDRA_DEVICE_SUPPORT)

        else()
        message(STATUS "-- *** RAZER HYDRA'S ROS PACKAGE NOT FOUND")
        endif()

    endif()
    include_directories(${catkin_INCLUDE_DIRS})
endif()

# Windows global build options
if (${CMAKE_SYSTEM_NAME} MATCHES Windows)

  # VisualStudio compiler
  if (MSVC)
      list(APPEND COMMON_DEFINITIONS -D_CRT_SECURE_NO_DEPRECATE)
        set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /EHsc /MP")
    if (${CMAKE_CL_64})
        list(APPEND COMMON_DEFINITIONS -DWIN64)
    else ()
      list(APPEND COMMON_DEFINITIONS -DWIN32)
    endif ()

  # MinGW compiler
  elseif (MINGW)
    list(APPEND COMMON_DEFINITIONS -DWIN32)
    list(APPEND CHAI3D_DEFINITIONS -DHAVE_GCC_DESTRUCTOR)
    set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=native -Wno-deprecated -std=c++0x")
    set (CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   -march=native -Wno-deprecated")
  endif ()

# Linux global build options
elseif (${CMAKE_SYSTEM_NAME} MATCHES Linux)
  list(APPEND COMMON_DEFINITIONS -DLINUX)
  set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC -march=native -Wno-deprecated -std=c++0x")
  set (CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   -fPIC -march=native -Wno-deprecated")

# Mac OS X global build options
elseif (${CMAKE_SYSTEM_NAME} MATCHES Darwin)
  list(APPEND COMMON_DEFINITIONS -DMACOSX)
  set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Qunused-arguments -Wno-deprecated -std=c++0x -stdlib=libc++")
  set (CMAKE_C_FLAGS   "${CMAKE_C_FLAGS}   -Qunused-arguments -Wno-deprecated")
endif ()

# on non-Windows, DHD dependency
if (NOT ${CMAKE_SYSTEM_NAME} MATCHES Windows)
  include_directories (${PROJECT_SOURCE_DIR}/external/DHD/include)
  if(${CMAKE_GENERATOR} STREQUAL Xcode)
    set (DHD_LIBRARY_DIRS ${PROJECT_SOURCE_DIR}/external/DHD/lib/${OS})
  else()
    set (DHD_LIBRARY_DIRS ${PROJECT_SOURCE_DIR}/external/DHD/lib/${OS}-${ARCH})
  endif()
  link_directories (${DHD_LIBRARY_DIRS})
endif ()

#
# static library
#

# Setting CMake to prepend rather than append include directories
set(CMAKE_INCLUDE_DIRECTORIES_BEFORE TRUE)

# GLFW
add_subdirectory (${PROJECT_SOURCE_DIR}/external/GLFW)

# GLFW Includes
include_directories (${GLFW_INCLUDE_DIRS})

# header search path
include_directories (${PROJECT_SOURCE_DIR}/ambf_math)
include_directories (${PROJECT_SOURCE_DIR}/adf_loader)
include_directories (${PROJECT_SOURCE_DIR}/ambf_plugins/core)
include_directories (${PROJECT_SOURCE_DIR}/ambf_framework)
include_directories (${PROJECT_SOURCE_DIR}/external/chai3d/src)
include_directories (${PROJECT_SOURCE_DIR}/external/bullet/src)
include_directories (${PROJECT_SOURCE_DIR}/external/Eigen)
include_directories (${PROJECT_SOURCE_DIR}/external/glew/include)
include_directories (${PROJECT_SOURCE_DIR}/external/giflib/include)
include_directories (${PROJECT_SOURCE_DIR}/external/lib3ds/include)
include_directories (${PROJECT_SOURCE_DIR}/external/libjpeg/include)
include_directories (${PROJECT_SOURCE_DIR}/external/libpng/include)
include_directories (${PROJECT_SOURCE_DIR}/external/openal/include)
include_directories (${PROJECT_SOURCE_DIR}/external/openal/OpenAL32/Include)
include_directories (${PROJECT_SOURCE_DIR}/external/openal/Alc)
include_directories (${PROJECT_SOURCE_DIR}/external/pugixml/include)
include_directories (${PROJECT_SOURCE_DIR}/external/theoraplayer/include/theoraplayer)
include_directories (${PROJECT_SOURCE_DIR}/external/theoraplayer/external/ogg/include)
include_directories (${PROJECT_SOURCE_DIR}/external/theoraplayer/external/theora/include)
include_directories (${PROJECT_SOURCE_DIR}/external/theoraplayer/external/vorbis/include)
include_directories (${PROJECT_SOURCE_DIR}/external/theoraplayer/external/vorbis/lib)
include_directories (${PROJECT_SOURCE_DIR}/external/theoraplayer/src/Theora)


# static library source files
file (GLOB_RECURSE source_ambf_math RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/ambf_math/*.cpp ${PROJECT_SOURCE_DIR}/ambf_math/*.h)
# static library source files
file (GLOB_RECURSE source_adf_loader RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/adf_loader/*.cpp ${PROJECT_SOURCE_DIR}/adf_loader/*.h)
# static library source files
file (GLOB_RECURSE source_ambf_plugins RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/ambf_plugins/core/*.cpp ${PROJECT_SOURCE_DIR}/ambf_plugins/core/*.h)
# static library source files
file (GLOB_RECURSE source_ambf_framework RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/ambf_framework/*.cpp ${PROJECT_SOURCE_DIR}/ambf_framework/*.h)

# static library external dependencies source files
file (GLOB_RECURSE source_chai3d  RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/chai3d/src/*.cpp ${PROJECT_SOURCE_DIR}/external/chai3d/src/*.h)

file (GLOB_RECURSE source_bullet_collision  RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/bullet/src/BulletCollision/*.cpp ${PROJECT_SOURCE_DIR}/external/bullet/src/BulletCollision/*.h)
file (GLOB_RECURSE source_bullet_dynamics   RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/bullet/src/BulletDynamics/*.cpp  ${PROJECT_SOURCE_DIR}/external/bullet/src/BulletDynamics/*.h)
file (GLOB_RECURSE source_bullet_softbody   RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/bullet/src/BulletSoftBody/*.cpp  ${PROJECT_SOURCE_DIR}/external/bullet/src/BulletSoftBody/*.h)
file (GLOB_RECURSE source_bullet_linearmath RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/bullet/src/LinearMath/*.cpp      ${PROJECT_SOURCE_DIR}/external/bullet/src/LinearMath/*.h)

# static library external dependencies source files
file (GLOB_RECURSE source_eigen     RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/Eigen/Eigen/*)
file (GLOB_RECURSE source_gif       RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/giflib/*.c       ${PROJECT_SOURCE_DIR}/external/giflib/*.h)
file (GLOB_RECURSE source_glew      RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/glew/*.c         ${PROJECT_SOURCE_DIR}/external/glew/*.h)
file (GLOB_RECURSE source_3ds       RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/lib3ds/*.c       ${PROJECT_SOURCE_DIR}/external/lib3ds/*.h)
file (GLOB_RECURSE source_jpeg      RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/libjpeg/*.c      ${PROJECT_SOURCE_DIR}/external/libjpeg/*.h)
file (GLOB_RECURSE source_png       RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/libpng/*.c       ${PROJECT_SOURCE_DIR}/external/libpng/*.h)
file (GLOB_RECURSE source_pugixml   RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/pugixml/*.c      ${PROJECT_SOURCE_DIR}/external/pugixml/*.h)
file (GLOB_RECURSE source_openal    RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/openal/*.c       ${PROJECT_SOURCE_DIR}/external/openal/*.h)
file (GLOB_RECURSE source_theora    RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/theoraplayer/*.c ${PROJECT_SOURCE_DIR}/external/theoraplayer/*.cpp ${PROJECT_SOURCE_DIR}/external/theoraplayer/*.h)
# build flags

# platform-specific source files adjustments
if (${CMAKE_SYSTEM_NAME} MATCHES Windows)
  file (GLOB_RECURSE source_theora_exclude RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/theoraplayer/external/theora/lib/x86/*.c)
else ()
  file (GLOB_RECURSE source_theora_exclude RELATIVE ${PROJECT_SOURCE_DIR} ${PROJECT_SOURCE_DIR}/external/theoraplayer/external/theora/lib/x86_vc/*.c)
endif ()
list (REMOVE_ITEM source_theora ${source_theora_exclude})

# group source files (MSVC likes this)
foreach (FILE ${source_ambf_framework} ${source_ambf_plugins} ${source_ambf_math} ${source_adf_loader} ${source_chai3d} ${source_eigen} ${source_gif} ${source_glew} ${source_3ds} ${source_jpeg} ${source_png} ${source_pugixml} ${source_openal} ${source_theora} ${source_bullet_collision} ${source_bullet_dynamics} ${source_bullet_softbody} ${source_bullet_linearmath})
  get_filename_component (PARENT_DIR "${FILE}" PATH)
  string (REGEX REPLACE "(\\./)?(src|include)/?" "" GROUP "${PARENT_DIR}")
  string (REPLACE "/" "\\" GROUP "${GROUP}")
  source_group ("${GROUP}" FILES "${FILE}")
endforeach ()

# internal library build flags
if (${CMAKE_BUILD_TYPE} MATCHES Debug)
  list(APPEND COMMON_DEFINITIONS -DDEBUG)
endif ()
if (${CMAKE_SIZEOF_VOID_P} EQUAL 8)
  if (NOT ${CMAKE_HOST_SYSTEM_PROCESSOR}  MATCHES "aarch64")
    list(APPEND BULLET_DEFINITIONS -DUSE_X86_64_ASM)
  endif ()
endif ()

# build flags
list(APPEND BULLET_DEFINITIONS -DBT_USE_DOUBLE_PRECISION)
list(APPEND CHAI3D_DEFINITIONS -DAL_ALEXT_PROTOTYPES -DAL_BUILD_LIBRARY -DAL_LIBTYPE_STATIC -D__THEORA -D_LIB)
list(APPEND COMMON_DEFINITIONS -DGLEW_STATIC)

# static library
add_library (adf_loader ${source_adf_loader})

if(NOT yaml-cpp_FOUND)
  add_dependencies(adf_loader YAML_CPP_EXTERNAL_PROJECT)
endif()

target_link_libraries(adf_loader ${YAML_CPP_LIBRARIES} ${Boost_LIBRARIES})

set (ADF_LOADER_LIBRARIES adf_loader)

add_subdirectory (${PROJECT_SOURCE_DIR}/tests)

add_library(chai3d STATIC ${source_chai3d} ${source_eigen} ${source_gif} ${source_glew} ${source_3ds} ${source_jpeg} ${source_png} ${source_pugixml} ${source_openal} ${source_theora})

add_library(bullet STATIC ${source_bullet_collision} ${source_bullet_dynamics} ${source_bullet_softbody} ${source_bullet_linearmath})

# static library
add_library (ambf_framework STATIC ${source_ambf_framework} ${source_ambf_plugins})

add_definitions(${CHAI3D_DEFINITIONS})
add_definitions(${BULLET_DEFINITIONS})
add_definitions(${AMBF_DEFINITIONS})
add_definitions(${COMMON_DEFINITIONS})
#target_compile_definitions(chai3d PUBLIC ${CHAI3D_DEFINITIONS} ${COMMON_DEFINITIONS})
#target_compile_definitions(bullet PUBLIC ${BULLET_DEFINITIONS} ${COMMON_DEFINITIONS})
#target_compile_definitions(ambf_framework PUBLIC ${AMBF_DEFINITIONS} ${COMMON_DEFINITIONS})

target_link_libraries(ambf_framework ${chai3d} ${bullet} ${Boost_LIBRARIES})

# To ensure the ambf_ros_modules are build before the ambf_framework,
# add catkin's targets as build dependency
 if (catkin_FOUND)
   add_dependencies(ambf_framework ${catkin_EXPORTED_TARGETS})
 endif()

# AMBF library exports
set (AMBF_INCLUDE_DIRS
    "${PROJECT_SOURCE_DIR}/adf_loader"
    "${PROJECT_SOURCE_DIR}/ambf_framework"
    "${PROJECT_SOURCE_DIR}/ambf_math"
    "${PROJECT_SOURCE_DIR}/external/bullet/src"
    "${PROJECT_SOURCE_DIR}/external/chai3d/src"
    "${PROJECT_SOURCE_DIR}/external/Eigen"
    "${PROJECT_SOURCE_DIR}/external/glew/include"
    "${GLFW_INCLUDE_DIRS}"
    "${OPENGL_INCLUDE_DIR}"
    "${Boost_INCLUDE_DIRS}")

set (AMBF_LIBRARIES ambf_framework chai3d bullet ${GLFW_LIBRARIES} ${OPENGL_LIBRARIES})
#set (AMBF_DEFINITIONS)

# ROS CATKIN INCLUDES AND LIBRARIES
if (${CMAKE_SYSTEM_NAME} MATCHES Linux)
    set (AMBF_INCLUDE_DIRS ${AMBF_INCLUDE_DIRS} ${AMBF_ROS_INCLUDE_DIRS})
endif()

if (NOT ${CMAKE_SYSTEM_NAME} MATCHES Windows)
  if (${CMAKE_HOST_SYSTEM_PROCESSOR}  MATCHES "aarch64")
#    set (AMBF_LIBRARIES ${AMBF_LIBRARIES})
  else ()
    set (AMBF_LIBRARIES ${AMBF_LIBRARIES} drd)
  endif ()
  set (AMBF_LIBRARY_DIRS ${AMBF_LIBRARY_DIRS} ${DHD_LIBRARY_DIRS})
else ()
  set (AMBF_LIBRARIES ${AMBF_LIBRARIES} winmm)
endif ()

if (${OS} MATCHES lin)
    set (AMBF_LIBRARIES ${AMBF_LIBRARIES} usb-1.0 rt pthread dl)
elseif (${OS} MATCHES mac)
  set (AMBF_LIBRARIES ${AMBF_LIBRARIES} "-framework CoreFoundation" "-framework IOKit" "-framework CoreServices" "-framework CoreAudio" "-framework AudioToolbox" "-framework AudioUnit")
endif ()

set (AMBF_SOURCE_DIR ${PROJECT_SOURCE_DIR})
#
# executables
#

# AMBF Simulator
add_subdirectory (${PROJECT_SOURCE_DIR}/ambf_simulator)


# AMBF Controller. Add if on Linux, Catkin Found and ambf_server Found
if (${CMAKE_SYSTEM_NAME} MATCHES Linux)
  if (catkin_FOUND AND ambf_server_FOUND)
    add_subdirectory (${PROJECT_SOURCE_DIR}/ambf_controller)
  endif()
endif()

#
# export package
#

# export package for use from the build tree
export (TARGETS ambf_framework ${ADF_LOADER_LIBRARIES} bullet chai3d glfw FILE ${PROJECT_BINARY_DIR}/AMBFTargets.cmake)
export (PACKAGE AMBF)

# configure package
set (CONF_INCLUDE_DIRS ${AMBF_INCLUDE_DIRS})
set (CONF_LIBRARY_DIRS  ${AMBF_LIBRARY_DIRS})
set (CONF_LIBRARIES  ${AMBF_LIBRARIES})
set (CONF_ROS_LIBRARIES  ${AMBF_ROS_LIBRARIES})
set (CONF_DEFINITIONS  ${AMBF_DEFINITIONS} ${CHAI3D_DEFINITIONS} ${BULLET_DEFINITIONS} ${COMMON_DEFINITIONS})

# create package configuration and version files
configure_file (AMBFConfig.cmake.in "${PROJECT_BINARY_DIR}/AMBFConfig.cmake" @ONLY)
configure_file (AMBFConfigVersion.cmake.in "${PROJECT_BINARY_DIR}/AMBFConfigVersion.cmake" @ONLY)
