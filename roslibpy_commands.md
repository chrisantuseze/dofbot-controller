# General commands
cd ~/echris/dofbot-controller
source ~/.bashrc
source /opt/ros/noetic/setup.bash
source ~/.bashrc
source dofbot_pro_ws/devel/setup.bash 
clear

# #################################################################################################
# ################### Keyboard Data Collection (pick-and-place demonstrations) ####################
# #################################################################################################

# Terminal #1 — ROS core
roscore

# Terminal #2 — Robot arm driver
rosrun dofbot_pro_info arm_driver.py

# Terminal #3 — Camera
roslaunch orbbec_camera dabai_dcw2.launch

# Terminal #4 — Allow the arm to accept commands
rostopic pub /robot/cmd std_msgs/String "data: 'start'"

# Terminal #5 — Data collector (saves HDF5 episodes)
roslaunch dofbot_policy_bridge keyboard_collection.launch \
    output_dir:=$HOME/echris/dofbot-controller/dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset \
    record_hz:=5 \
    episode_index:=0

# Terminal #6 — Keyboard teleop (must run in its own interactive terminal)
rosrun dofbot_policy_bridge keyboard_teleop.py

# ── Key layout ────────────────────────────────────────────────────────────────
#   Hold to move joint: - L/R: Right is for downwards motion, Left is upwards
#     j0 base          a / d
#     j1 shoulder      w / s
#     j2 elbow         r / f
#     j3 wrist pitch   t / g
#     j4 wrist twist   y / h
#     j5 gripper       o (open) / c (close)
#
#   Episode control (single press):
#     [  start recording
#     ]  stop + save  →  writes HDF5 to output_dir
#     \  discard + home
#     z  home only
#     x  place position
#     p  print current joint angles
#     q  quit


# #################################################################################################
# ############## Gamepad Data Collection (pick-and-place demonstrations) ##########################
# #################################################################################################

# Prereq: plug in the USB gamepad controller.
# Install pygame if not already installed:
pip install pygame

# Terminal #1 — ROS core
roscore

# Terminal #2 — Robot arm driver (publishes joint states, drives servos)
rosrun dofbot_pro_info arm_driver.py

# Terminal #3 — Camera
roslaunch orbbec_camera dabai_dcw2.launch

# Terminal #4 — Allow the arm to accept commands (does NOT start recording)
# Use -1 to publish once and exit, so the latched message doesn't auto-start recording
rostopic pub -1 /robot/cmd std_msgs/String "data: 'start'"

# Terminal #5 — Start gamepad teleop + data collector together
roslaunch dofbot_policy_bridge data_collection.launch \
    output_dir:=$HOME/echris/dofbot-controller/dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset \
    episode_index:=0

# Override gamepad speed or starting episode:
roslaunch dofbot_policy_bridge data_collection.launch \
    output_dir:=$HOME/dofbot_dataset \
    episode_index:=10 \
    speed_dps:=45

# ── Gamepad button / axis layout (confirmed) ──────────────────────────────────
#   Left  stick X     (axis 0)      → j0  base rotation
#   Left  stick Y     (axis 1)      → j1  shoulder  (north = joint up)
#   Right stick Y     (axis 3)      → j3  wrist pitch (north = joint down)
#   Right stick east  (axis 5 +)    → j5  gripper open
#   btn_gripper_close (held)        → j5  gripper close  (default btn 4)
#   Y button (btn 3, held)          → j4  positive direction
#   j2 is not controlled via the gamepad.
#
#   A  (btn 0) — Start recording
#   B  (btn 1) — Stop + save episode
#   X  (btn 2) — Discard current episode + move arm to home
#
# ── Workflow per episode ──────────────────────────────────────────────────────
#   1. Position the object on the table.
#   2. Jog the arm to the start pose using the sticks.
#   3. Press A to begin recording.
#   4. Perform the pick-and-place.
#   5. Press B to save (or X to discard and retry).
#   6. Press Y to reset the arm to home before the next episode.
#
# ── Episode files ─────────────────────────────────────────────────────────────
#   ~/dofbot_dataset/episode_000000.hdf5
#   ~/dofbot_dataset/episode_000001.hdf5  ...
#
#   Each file contains:
#     observation/images/top   (T, 224, 224, 3) uint8 RGB
#     observation/state        (T, 6)  float32  joint angles in radians
#     action                   (T, 6)  float32  commanded angles in radians
#
# ── Remapping axes for a different controller ─────────────────────────────────
#   First, identify button / axis indices with the test script (no ROS needed):
#     python3 dofbot_pro_ws/src/dofbot_policy_bridge/scripts/test_gamepad.py
#
#   Then override btn_gripper_close if the gripper-close button differs:
#     roslaunch dofbot_policy_bridge data_collection.launch btn_gripper_close:=6

# #################################################################################################
# ########################### INFERENCE ######################
# #################################################################################################
## LeRobot / Open Policy Models (lerobot_inference_server.py)
# Jetson terminals 1–5 are the same as above (roscore, rosbridge, arm_driver, camera)

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
# Use -1 to publish once and exit, so the latched message doesn't auto-start recording
rostopic pub -1 /robot/cmd std_msgs/String "data: 'start'"

## Jetson terminal #7 - Robot controller (safety gate + episode management)
rosrun dofbot_policy_bridge robot_controller.py

## FINALLY 
## Lab Computer — Step 1: smoke test (no ML, validates full pipeline)
python lerobot_inference_server.py \
    --policy_type mock \
    --inference_hz 0.2 \
    --move_time_ms 2000 \
    --jetson_ip 192.168.0.8

## Lab Computer — Step 3: your fine-tuned checkpoint
python3 inference/lerobot_inference_server.py \
    --policy_type act \
    --checkpoint_path training/runs/act_001/checkpoints/step_005000 \
    --inference_hz 5 \
    --move_time_ms 200 \
    --jetson_ip 192.168.0.8


# #################################################################################################
# ####################### FINETUNING #######################
# #################################################################################################

# Quick pipeline test (overfits 2 episodes — expected):
python training/train_act.py \
  --dataset_dir dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset \
  --num_steps 5000 --save_freq 1000

# Full training run (after collecting 50+ demos):
python training/train_act.py \
    --dataset_dir dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset \
    --output_dir runs/act_001 --num_steps 50000 --device cuda

Ctrl + Z to stop a program from running