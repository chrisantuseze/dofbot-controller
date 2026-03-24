# Install script for directory: /home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_voice_ctrl

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/jetson/echris/object-unveiler/dofbot_pro_ws/install")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/dofbot_pro_voice_ctrl" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/include/dofbot_pro_voice_ctrl/ColorHSVConfig.h")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/dist-packages/dofbot_pro_voice_ctrl" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/lib/python3/dist-packages/dofbot_pro_voice_ctrl/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  execute_process(COMMAND "/usr/bin/python3" -m compileall "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/lib/python3/dist-packages/dofbot_pro_voice_ctrl/cfg")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/dist-packages/dofbot_pro_voice_ctrl" TYPE DIRECTORY FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/lib/python3/dist-packages/dofbot_pro_voice_ctrl/cfg")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_voice_ctrl/catkin_generated/installspace/dofbot_pro_voice_ctrl.pc")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_voice_ctrl/cmake" TYPE FILE FILES
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_voice_ctrl/catkin_generated/installspace/dofbot_pro_voice_ctrlConfig.cmake"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_voice_ctrl/catkin_generated/installspace/dofbot_pro_voice_ctrlConfig-version.cmake"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_voice_ctrl" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_voice_ctrl/package.xml")
endif()

