# generated from genmsg/cmake/pkg-genmsg.cmake.em

message(STATUS "dofbot_pro_info: 12 messages, 3 services")

set(MSG_I_FLAGS "-Idofbot_pro_info:/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg;-Iactionlib_msgs:/opt/ros/noetic/share/actionlib_msgs/cmake/../msg;-Igeometry_msgs:/opt/ros/noetic/share/geometry_msgs/cmake/../msg;-Isensor_msgs:/opt/ros/noetic/share/sensor_msgs/cmake/../msg;-Istd_msgs:/opt/ros/noetic/share/std_msgs/cmake/../msg")

# Find all generators
find_package(gencpp REQUIRED)
find_package(geneus REQUIRED)
find_package(genlisp REQUIRED)
find_package(gennodejs REQUIRED)
find_package(genpy REQUIRED)

add_custom_target(dofbot_pro_info_generate_messages ALL)

# verify that message/service dependencies have not changed since configure



get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg" "std_msgs/Header:sensor_msgs/Image"
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg" "std_msgs/Header:sensor_msgs/Image"
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv" ""
)

get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv" NAME_WE)
add_custom_target(_dofbot_pro_info_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "dofbot_pro_info" "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv" ""
)

#
#  langs = gencpp;geneus;genlisp;gennodejs;genpy
#

### Section generating for lang: gencpp
### Generating Messages
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)

### Generating Services
_generate_srv_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_cpp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
)

### Generating Module File
_generate_module_cpp(dofbot_pro_info
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
  "${ALL_GEN_OUTPUT_FILES_cpp}"
)

add_custom_target(dofbot_pro_info_generate_messages_cpp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_cpp}
)
add_dependencies(dofbot_pro_info_generate_messages dofbot_pro_info_generate_messages_cpp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_cpp _dofbot_pro_info_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(dofbot_pro_info_gencpp)
add_dependencies(dofbot_pro_info_gencpp dofbot_pro_info_generate_messages_cpp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS dofbot_pro_info_generate_messages_cpp)

### Section generating for lang: geneus
### Generating Messages
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)

### Generating Services
_generate_srv_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_eus(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
)

### Generating Module File
_generate_module_eus(dofbot_pro_info
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
  "${ALL_GEN_OUTPUT_FILES_eus}"
)

add_custom_target(dofbot_pro_info_generate_messages_eus
  DEPENDS ${ALL_GEN_OUTPUT_FILES_eus}
)
add_dependencies(dofbot_pro_info_generate_messages dofbot_pro_info_generate_messages_eus)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_eus _dofbot_pro_info_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(dofbot_pro_info_geneus)
add_dependencies(dofbot_pro_info_geneus dofbot_pro_info_generate_messages_eus)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS dofbot_pro_info_generate_messages_eus)

### Section generating for lang: genlisp
### Generating Messages
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)

### Generating Services
_generate_srv_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_lisp(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
)

### Generating Module File
_generate_module_lisp(dofbot_pro_info
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
  "${ALL_GEN_OUTPUT_FILES_lisp}"
)

add_custom_target(dofbot_pro_info_generate_messages_lisp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_lisp}
)
add_dependencies(dofbot_pro_info_generate_messages dofbot_pro_info_generate_messages_lisp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_lisp _dofbot_pro_info_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(dofbot_pro_info_genlisp)
add_dependencies(dofbot_pro_info_genlisp dofbot_pro_info_generate_messages_lisp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS dofbot_pro_info_generate_messages_lisp)

### Section generating for lang: gennodejs
### Generating Messages
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)

### Generating Services
_generate_srv_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_nodejs(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
)

### Generating Module File
_generate_module_nodejs(dofbot_pro_info
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
  "${ALL_GEN_OUTPUT_FILES_nodejs}"
)

add_custom_target(dofbot_pro_info_generate_messages_nodejs
  DEPENDS ${ALL_GEN_OUTPUT_FILES_nodejs}
)
add_dependencies(dofbot_pro_info_generate_messages dofbot_pro_info_generate_messages_nodejs)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_nodejs _dofbot_pro_info_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(dofbot_pro_info_gennodejs)
add_dependencies(dofbot_pro_info_gennodejs dofbot_pro_info_generate_messages_nodejs)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS dofbot_pro_info_generate_messages_nodejs)

### Section generating for lang: genpy
### Generating Messages
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_msg_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/sensor_msgs/cmake/../msg/Image.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)

### Generating Services
_generate_srv_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)
_generate_srv_py(dofbot_pro_info
  "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
)

### Generating Module File
_generate_module_py(dofbot_pro_info
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
  "${ALL_GEN_OUTPUT_FILES_py}"
)

add_custom_target(dofbot_pro_info_generate_messages_py
  DEPENDS ${ALL_GEN_OUTPUT_FILES_py}
)
add_dependencies(dofbot_pro_info_generate_messages dofbot_pro_info_generate_messages_py)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/joint_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/pos_info.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Position.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/CenterXY.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/AprilTagInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ShapeInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/WidthInfo.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ArmJoint.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Image_Msg.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/Yolov5Detect.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ActionData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/msg/ObservData.msg" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/cur_joint.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/jetson/echris/object-unveiler/dofbot_pro_ws/src/dofbot_pro_info/srv/dofbot_pro_kinemarics.srv" NAME_WE)
add_dependencies(dofbot_pro_info_generate_messages_py _dofbot_pro_info_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(dofbot_pro_info_genpy)
add_dependencies(dofbot_pro_info_genpy dofbot_pro_info_generate_messages_py)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS dofbot_pro_info_generate_messages_py)



if(gencpp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/dofbot_pro_info
    DESTINATION ${gencpp_INSTALL_DIR}
  )
endif()
if(TARGET actionlib_msgs_generate_messages_cpp)
  add_dependencies(dofbot_pro_info_generate_messages_cpp actionlib_msgs_generate_messages_cpp)
endif()
if(TARGET geometry_msgs_generate_messages_cpp)
  add_dependencies(dofbot_pro_info_generate_messages_cpp geometry_msgs_generate_messages_cpp)
endif()
if(TARGET sensor_msgs_generate_messages_cpp)
  add_dependencies(dofbot_pro_info_generate_messages_cpp sensor_msgs_generate_messages_cpp)
endif()
if(TARGET std_msgs_generate_messages_cpp)
  add_dependencies(dofbot_pro_info_generate_messages_cpp std_msgs_generate_messages_cpp)
endif()

if(geneus_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/dofbot_pro_info
    DESTINATION ${geneus_INSTALL_DIR}
  )
endif()
if(TARGET actionlib_msgs_generate_messages_eus)
  add_dependencies(dofbot_pro_info_generate_messages_eus actionlib_msgs_generate_messages_eus)
endif()
if(TARGET geometry_msgs_generate_messages_eus)
  add_dependencies(dofbot_pro_info_generate_messages_eus geometry_msgs_generate_messages_eus)
endif()
if(TARGET sensor_msgs_generate_messages_eus)
  add_dependencies(dofbot_pro_info_generate_messages_eus sensor_msgs_generate_messages_eus)
endif()
if(TARGET std_msgs_generate_messages_eus)
  add_dependencies(dofbot_pro_info_generate_messages_eus std_msgs_generate_messages_eus)
endif()

if(genlisp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/dofbot_pro_info
    DESTINATION ${genlisp_INSTALL_DIR}
  )
endif()
if(TARGET actionlib_msgs_generate_messages_lisp)
  add_dependencies(dofbot_pro_info_generate_messages_lisp actionlib_msgs_generate_messages_lisp)
endif()
if(TARGET geometry_msgs_generate_messages_lisp)
  add_dependencies(dofbot_pro_info_generate_messages_lisp geometry_msgs_generate_messages_lisp)
endif()
if(TARGET sensor_msgs_generate_messages_lisp)
  add_dependencies(dofbot_pro_info_generate_messages_lisp sensor_msgs_generate_messages_lisp)
endif()
if(TARGET std_msgs_generate_messages_lisp)
  add_dependencies(dofbot_pro_info_generate_messages_lisp std_msgs_generate_messages_lisp)
endif()

if(gennodejs_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/dofbot_pro_info
    DESTINATION ${gennodejs_INSTALL_DIR}
  )
endif()
if(TARGET actionlib_msgs_generate_messages_nodejs)
  add_dependencies(dofbot_pro_info_generate_messages_nodejs actionlib_msgs_generate_messages_nodejs)
endif()
if(TARGET geometry_msgs_generate_messages_nodejs)
  add_dependencies(dofbot_pro_info_generate_messages_nodejs geometry_msgs_generate_messages_nodejs)
endif()
if(TARGET sensor_msgs_generate_messages_nodejs)
  add_dependencies(dofbot_pro_info_generate_messages_nodejs sensor_msgs_generate_messages_nodejs)
endif()
if(TARGET std_msgs_generate_messages_nodejs)
  add_dependencies(dofbot_pro_info_generate_messages_nodejs std_msgs_generate_messages_nodejs)
endif()

if(genpy_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info)
  install(CODE "execute_process(COMMAND \"/usr/bin/python3\" -m compileall \"${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info\")")
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/dofbot_pro_info
    DESTINATION ${genpy_INSTALL_DIR}
  )
endif()
if(TARGET actionlib_msgs_generate_messages_py)
  add_dependencies(dofbot_pro_info_generate_messages_py actionlib_msgs_generate_messages_py)
endif()
if(TARGET geometry_msgs_generate_messages_py)
  add_dependencies(dofbot_pro_info_generate_messages_py geometry_msgs_generate_messages_py)
endif()
if(TARGET sensor_msgs_generate_messages_py)
  add_dependencies(dofbot_pro_info_generate_messages_py sensor_msgs_generate_messages_py)
endif()
if(TARGET std_msgs_generate_messages_py)
  add_dependencies(dofbot_pro_info_generate_messages_py std_msgs_generate_messages_py)
endif()
