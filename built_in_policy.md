cd ~/echris/dofbot-controller
source ~/.bashrc
source /opt/ros/noetic/setup.bash
source ~/.bashrc
source dofbot_pro_ws/devel/setup.bash 
clear

# Terminal 1 — ROS core
roscore

# Terminal 2 — Arm driver
rosrun dofbot_pro_info arm_driver.py

# Terminal 3 — Camera (RGB + depth)
roslaunch orbbec_camera dabai_dcw2.launch

# Terminal 4 — IK kinematics service (needed by color_grasp_VC.py)
rosrun dofbot_pro_info kinemarics_dofbot_pro

# Terminal 5 — Color detector (pass target color via voice_result topic or set default)
rosrun dofbot_pro_voice_ctrl lang_color_detect.py

# Terminal 6 — Grasp executor
rosrun dofbot_pro_voice_ctrl lang_color_grasp.py

# Tell the detector to look for red:
rostopic pub -1 /voice_result std_msgs/Int8 "data: 7"   # 7=red, 8=green, 9=blue, 10=yellow

# Terminal 7 — rosbridge (needed only when the Verify2Act pipeline runs from another machine / via roslibpy)
roslaunch rosbridge_server rosbridge_websocket.launch

# Terminal 8 — Verify2Act session: ONE task, N episodes (each episode: reset scene -> Enter -> run -> answer y/n)
#   presets: task1a (blue+yellow -> bin) | task1b (green+blue -> bin, leave rest) | task1c (warm -> bin, leave green) | task1d (red+green+blue -> bin, leave yellow) | task3a (stack blue on yellow)
python3 verify2act/v2a_session.py --task task1a --episodes 10 --jetson_ip 127.0.0.1
python3 verify2act/v2a_session.py --task task3a --episodes 10 --jetson_ip 127.0.0.1
python3 verify2act/v2a_session.py --task task1b --episodes 3 --jetson_ip 127.0.0.1 --dry_run   # real camera, arm never moves
# Results: verify2act/results/<task>_<time>/summary.md  (+ episodes.jsonl and per-episode images)

# Single episode without a session (quick test):
python3 verify2act/v2a_pipeline.py --task task1b --jetson_ip 127.0.0.1

# Tune where the block is dropped in the bin (live, no restart): j1 base, then j2..j6
rosparam set /lang_color_grasp/drop_left_bin "[150, 60, 30, 16, 90, 135]"
# Tune stacking height (metres added above the detected top of the base block; lower = closer)
rosparam set /lang_color_grasp/stack_dz 0.05

# World model + critic on a separate GPU machine (the Jetson cannot run them; needs rosbridge on this Jetson)
#   GPU machine (verify2act research repo, branch robot-server):
#     python3 -m verify2act.robot.robot_server --jetson_ip <JETSON_IP> --critic-ckpt ... --latent-wm-ckpt ... --encoder-ckpt ...
#   Jetson: same commands as above plus --wm_server
python3 verify2act/v2a_session.py --task task3a --episodes 10 --jetson_ip 127.0.0.1 --wm_server
#   Test the round trip without a GPU box (stub models served over rosbridge):
python3 verify2act/remote/v2a_server.py --jetson_ip 127.0.0.1
