# Install script for directory: /home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_KCF

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
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/dofbot_pro_KCF" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/include/dofbot_pro_KCF/KCFTrackerConfig.h")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/dofbot_pro_KCF" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/include/dofbot_pro_KCF/ColorTrackerPIDConfig.h")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/dofbot_pro_KCF" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/include/dofbot_pro_KCF/ColorHSVConfig.h")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/dist-packages/dofbot_pro_KCF" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/lib/python3/dist-packages/dofbot_pro_KCF/__init__.py")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  execute_process(COMMAND "/usr/bin/python3" -m compileall "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/lib/python3/dist-packages/dofbot_pro_KCF/cfg")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/dist-packages/dofbot_pro_KCF" TYPE DIRECTORY FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/lib/python3/dist-packages/dofbot_pro_KCF/cfg")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_KCF/catkin_generated/installspace/dofbot_pro_KCF.pc")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_KCF/cmake" TYPE FILE FILES
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_KCF/catkin_generated/installspace/dofbot_pro_KCFConfig.cmake"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_KCF/catkin_generated/installspace/dofbot_pro_KCFConfig-version.cmake"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_KCF" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_KCF/package.xml")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_KCF/include/dofbot_pro_KCF/cmake_install.cmake")

endif()

