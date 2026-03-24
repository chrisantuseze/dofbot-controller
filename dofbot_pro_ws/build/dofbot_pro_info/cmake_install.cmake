# Install script for directory: /home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info

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
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_info/msg" TYPE FILE FILES
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_info/srv" TYPE FILE FILES
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_info/cmake" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_info/catkin_generated/installspace/dofbot_pro_info-msg-paths.cmake")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include" TYPE DIRECTORY FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/include/dofbot_pro_info")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/roseus/ros" TYPE DIRECTORY FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/share/roseus/ros/dofbot_pro_info")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/common-lisp/ros" TYPE DIRECTORY FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/share/common-lisp/ros/dofbot_pro_info")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/gennodejs/ros" TYPE DIRECTORY FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/share/gennodejs/ros/dofbot_pro_info")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  execute_process(COMMAND "/usr/bin/python3" -m compileall "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/lib/python3/dist-packages/dofbot_pro_info")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3/dist-packages" TYPE DIRECTORY FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/devel/lib/python3/dist-packages/dofbot_pro_info")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/pkgconfig" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_info/catkin_generated/installspace/dofbot_pro_info.pc")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_info/cmake" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_info/catkin_generated/installspace/dofbot_pro_info-msg-extras.cmake")
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_info/cmake" TYPE FILE FILES
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_info/catkin_generated/installspace/dofbot_pro_infoConfig.cmake"
    "/home/jetson/echris/object-unveiler/dofbot_pro_ws/build/dofbot_pro_info/catkin_generated/installspace/dofbot_pro_infoConfig-version.cmake"
    )
endif()

if("x${CMAKE_INSTALL_COMPONENT}x" STREQUAL "xUnspecifiedx" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/dofbot_pro_info" TYPE FILE FILES "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/package.xml")
endif()

