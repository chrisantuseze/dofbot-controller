cmake_minimum_required(VERSION 3.0.2)
project(dofbot_policy_bridge)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  cv_bridge
  yahboomcar_msgs
  dofbot_pro_info
)

catkin_package()

install(PROGRAMS
  scripts/data_collector.py
  scripts/robot_controller.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
