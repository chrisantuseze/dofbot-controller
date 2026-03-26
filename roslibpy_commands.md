# General commands
cd ~/echris/dofbot-controller
source ~/.bashrc
source /opt/ros/noetic/setup.bash
source ~/.bashrc
source dofbot_pro_ws/devel/setup.bash 
clear

## LeRobot / Open Policy Models (lerobot_inference_server.py)
# Jetson terminals 1–5 are the same as above (roscore, rosbridge, arm_driver, camera)
# Do NOT run terminal #6 (unveiler_grasp.py) — the inference server replaces it.

## Jetson terminal #1
roscore

## Jetson terminal #2 - Starts the ros bridge websocket
roslaunch rosbridge_server rosbridge_websocket.launch

## Jetson terminal #3 - Computes (inverse) kinematics (optional — only needed if using IK)
rosrun dofbot_pro_info kinemarics_dofbot_pro

## Jetson terminal #4 - Publishes joint values to drive robot joints
rosrun dofbot_pro_info arm_driver.py

## Jetson terminal #5 - Start camera topic
roslaunch orbbec_camera dabai_dcw2.launch

## Jetson terminal #6 - Start command for the robot side to work.
rostopic pub /robot/cmd std_msgs/String "data: 'start'"

## Jetson terminal #7 - Robot controller (safety gate + episode management)
rosrun dofbot_policy_bridge robot_controller.py

## FINALLY 
## Lab Computer — Step 1: smoke test (no ML, validates full pipeline)
python lerobot_inference_server.py \
    --policy_type mock \
    --inference_hz 0.2 \
    --move_time_ms 2000 \
    --jetson_ip 192.168.0.8

## Lab Computer — Step 2: pretrained HuggingFace model (no training needed)
pip install lerobot
python lerobot_inference_server.py \
    --policy_type pretrained \
    --pretrained_repo lerobot/act_koch_real \
    --inference_hz 10 \
    --move_time_ms 200 \
    --jetson_ip 192.168.0.8

## Lab Computer — Step 3: your fine-tuned checkpoint
python lerobot_inference_server.py \
    --policy_type act \
    --checkpoint_path /path/to/your/checkpoint \
    --inference_hz 10 \
    --move_time_ms 200 \
    --jetson_ip 192.168.0.8


Ctrl + Z to stop a program from running