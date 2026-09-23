# Task 1 Demo Guide — Blocked Target + Obstacle Clearance

This document covers the complete workflow for recording and replaying the
Task 1 scripted demo for the CoRL supplementary video.

**Task setup:** 3 cubes on the table — **Target** (red), **Blocker 1** (blue),
**Blocker 2** (green). Blockers placed directly in front of the red cube.

---

## Step 0 — Prerequisites

Install Python dependencies on the lab computer (if not already done):

```bash
conda activate dofbot_controller
pip install roslibpy h5py opencv-python Pillow
```

---

## Step 1 — Start the Jetson Stack

Open these terminals **on the Jetson** (or SSH in, one per terminal):

```bash
# Terminal 1 — ROS core
roscore

# Terminal 2 — Arm driver (drives servos, publishes joint_states)
rosrun dofbot_pro_info arm_driver.py

# Terminal 3 — Camera
roslaunch orbbec_camera dabai_dcw2.launch

# Terminal 4 — rosbridge WebSocket (needed for lab-computer replay)
roslaunch rosbridge_server rosbridge_websocket.launch

# Terminal 5 — Safety gate + episode lifecycle
rosrun dofbot_policy_bridge robot_controller.py _gripper_soft_max_deg:=120

# Terminal 6 — Allow the arm to accept commands
rostopic pub -1 /robot/cmd std_msgs/String "data: 'start'"

```

---

## Step 2 — Start the Data Collector (Lab Computer)

Open a terminal **on the lab computer** (or any Jetson terminal with keyboard):

```bash
cd ~/echris/dofbot-controller
source ~/.bashrc
source /opt/ros/noetic/setup.bash
source dofbot_pro_ws/devel/setup.bash

# Start data collector — saves to the existing dataset directory
roslaunch dofbot_policy_bridge keyboard_collection.launch \
    output_dir:=$HOME/echris/dofbot-controller/verify2act/dataset \
    record_hz:=10 \
    episode_index:=0
    
```

> **Note:** Set `episode_index` to the next available index (check how many
> `episode_*.hdf5` files exist: `ls dofbot_dataset/ | wc -l`).

---

## Step 3 — Record the Failure Demo

**Scene:** Place blockers directly in front of the red cube so a direct grasp
is impossible.

**What to record:** The robot reaches toward the red cube but stops short,
showing that the direct path is blocked. This is _Attempt 1_ — the naive plan
that gets REJECTED by the critic.

```bash
# In a separate terminal — keyboard teleop
rosrun dofbot_policy_bridge keyboard_teleop.py
```

**Recording sequence:**

| Key | Action |
|-----|--------|
| `[` | **Start recording** |
| `w/s/r/f/t/g/a/d` | Steer arm toward the red cube (stop ~5 cm short) |
| `]` | **Stop + save** — when prompted for object label, type: `failure: reach blocked target` |

**Tips:**
- Move slowly and deliberately — the recording captures every intermediate position
- Stop the arm while it is visually "blocked" by the blue/green cubes
- You don't need a physical collision — just a believable stopped approach

---

## Step 4 — Record the Success Demo

**Scene:** Same table setup — blockers still in front of red cube.

**What to record:** A complete obstacle clearance sequence:
1. Clear blue blocker → move to left clear zone
2. Clear green blocker → move to right clear zone
3. Pick and place red cube → target zone

```bash
# Still in keyboard teleop (or restart if you quit)
rosrun dofbot_policy_bridge keyboard_teleop.py
```

**Recording sequence:**

| Step | Action | Key sequence |
|------|--------|-------------|
| Start | Begin recording | `[` |
| 1a | Move to hover above blue cube | `w/s/r/f/a/d` to position |
| 1b | Descend to grasp height | `s` (shoulder down) |
| 1c | Close gripper | `c` |
| 1d | Lift blue cube | `w` (shoulder up) |
| 1e | Move to left clear zone | `a/d` (base rotate) |
| 1f | Lower, open gripper | `s` then `o` |
| 1g | Lift away | `w` |
| 2a | Repeat for green cube → right clear zone | same pattern |
| 3a | Hover above red cube | position arm over red |
| 3b | Descend, close gripper, lift | `s`, `c`, `w` |
| 3c | Move to target zone, open gripper | `a/d`, `s`, `o` |
| End | Stop + save | `]` → label: `success: obstacle clearance pick place` |

**Keyboard layout reminder:**
```
j0 base        a (CCW) / d (CW)
j1 shoulder    w (up)  / s (down)
j2 elbow       r (up)  / f (down)
j3 wrist-pitch t (up)  / g (down)
j4 wrist-twist y (+)   / h (-)
j5 gripper     o (open)/ c (close)

[  start recording
]  stop + save (prompts for object label)
\  discard + home
z  go home
p  print current joint angles
```

---

## Step 5 — Verify the Recordings

Check the HDF5 files were saved correctly:

```bash
cd ~/echris/dofbot-controller

# List new episodes
ls -lh verify2act/dataset/episode_000{00,01}*

# Read episode metadata
python3 dofbot_pro_ws/src/dofbot_policy_bridge/scripts/read_episode.py \
    verify2act/dataset/episode_000000.hdf5

# Render to video for visual check (no robot needed)
python3 verify2act/replay_episode.py \
    verify2act/dataset/episode_000000.hdf5 \
    --show_joints
```

Open `episode_000000.mp4` (written alongside the HDF5) to visually verify the motion.

---

## Step 6 — Replay on Robot (For Video Recording)

With the physical robot and camera set up for filming:

### Safety test first (no objects on table)

```bash
# Half speed, go home after — run this before putting objects on table
python3 verify2act/replay_on_robot.py \
    dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000040.hdf5 \
    --speed 0.5 --home_after --jetson_ip 192.168.0.8
```

### Failure demo (Attempt 1 replay)

```bash
# Failure episode — place blockers in front of red cube
python3 verify2act/replay_on_robot.py \
    verify2act/dataset/episode_000000.hdf5 \
    --speed 0.4 --wait_for_ready \
    --gripper_max_deg 118 --gripper_margin_deg 2 \
    --home_after --jetson_ip 192.168.0.8
```

### Success demo (Attempt 2 replay)

```bash
# Success episode — same scene setup
python3 verify2act/replay_on_robot.py \
    verify2act/dataset/episode_000001.hdf5 \
    --speed 0.4 --wait_for_ready \
    --gripper_max_deg 118 --gripper_margin_deg 2 \
    --home_after --jetson_ip 127.0.0.1
```

> **Speed tuning:** Start at `--speed 0.3` if the motion looks jerky.
> Increase to `0.5`–`0.8` once it looks smooth. `1.0` = original recorded speed.

---

## Step 7 — Generate Overlay Card Graphics

```bash
python3 verify2act/overlay_cards.py
```

Outputs:
- `verify2act/assets/card_reject_attempt1.png` — red REJECTED card
- `verify2act/assets/card_accept_attempt2.png` — green ACCEPTED card

Custom scores:
```bash
python3 verify2act/overlay_cards.py \
    --reject_scores 0.12 0.31 \
    --accept_scores 0.87 0.91 \
    --reflect_reason "Path blocked by blue and green cubes"
```

---

## Step 8 — Render Episode Videos

```bash
# Render both demo episodes to .mp4 for the video
python3 verify2act/replay_episode.py \
    dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000040.hdf5

python3 verify2act/replay_episode.py \
    dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000041.hdf5 \
    --show_joints
```

---

## Post-Production Overlay Timeline

Per the `video_submission_guide.md` storyboard:

| Video timestamp | Content |
|----------------|---------|
| 0 s | Hook — cut in the failure replay |
| ~3 s | Overlay `card_reject_attempt1.png` (red border + REJECT card) |
| ~5 s | Overlay scripted VLM Plan text (Attempt 1) |
| ~8 s | Transition to success replay |
| ~15 s | Overlay `card_accept_attempt2.png` (green border + ACCEPT card) |
| ~18 s | Overlay scripted VLM Plan text (Attempt 2 — Reflected) |
| End | Climax clip: robot picks red cube successfully |

**Scripted VLM Plan text for overlays** (from `video_submission_guide.md`):

```
VLM Plan (Attempt 1):
  Step 1: Move to red cube
  Step 2: Grasp red cube
  Step 3: Place red cube at target zone

VLM Plan (Attempt 2 — Reflected):
  Step 1: Move blue cube → left clear zone
  Step 2: Move green cube → right clear zone
  Step 3: Move to red cube (now unobstructed)
  Step 4: Grasp red cube
  Step 5: Place red cube at target zone
```

---

## Quick Reference

```bash
# Record
rosrun dofbot_policy_bridge keyboard_teleop.py

# Render offline video
python3 verify2act/replay_episode.py <episode.hdf5> [--show_joints]

# Replay on robot
python3 verify2act/replay_on_robot.py <episode.hdf5> \
    --speed 0.4 --wait_for_ready --gripper_max_deg 118 --home_after \
    --jetson_ip 192.168.0.8

# Generate overlay cards
python3 verify2act/overlay_cards.py
```

---

## Verify2Act pipeline (VLM → world model → critic → grasp)

The planner, world model and critic run on any machine; the Jetson only runs ROS.

```bash
# Jetson: roscore, arm_driver, camera, rosbridge_websocket, then
rosrun dofbot_pro_voice_ctrl lang_color_detect.py
rosrun dofbot_pro_voice_ctrl lang_color_grasp.py

# Workstation (needs `pip install roslibpy opencv-python numpy`):
python3 verify2act/v2a_pipeline.py --task task1a --dry_run                       # offline, synthetic scene
python3 verify2act/v2a_pipeline.py --task task1a --jetson_ip <JETSON_IP> --dry_run  # real camera, no arm motion
python3 verify2act/v2a_pipeline.py --task task1a --jetson_ip <JETSON_IP>            # full run
```

Per-attempt results are appended to `verify2act/assets/rollouts/runs.jsonl`; after a real run the
post-execution frame is saved as `attempt_N_real_final.jpg` next to the imagined timeline.
Add `--simulate_reprompt` / `--simulate_temporal_inconsistency` to exercise the reject → retry paths.
