#!/usr/bin/env python3
"""
replay_on_robot.py
==================
Replay a recorded HDF5 episode on the real DofBot by publishing the stored
action commands through rosbridge — the same path used by the inference server.

Useful for:
  • Verifying a demo was recorded cleanly (the robot re-executes it exactly).
  • Diagnosing whether poor policy performance is a data-quality issue vs. a
    model issue (if the replay looks wrong, the demos themselves are the problem).

Architecture (mirrors lerobot_inference_server.py)
──────────────────────────────────────────────────
  Lab computer                    Jetson
  ────────────────                ──────────────────────────────
  replay_on_robot.py ─── WS ────→ rosbridge_websocket
                                    ↓ /robot/cmd   → robot_controller.py
                                    ↓ /policy/action → arm_driver.py (via ctrl)
                                    ↑ /robot/ready  ← robot_controller.py

Prerequisites (Jetson)
──────────────────────
  Terminal 1:  roscore
  Terminal 2:  rosrun dofbot_pro_info arm_driver.py
  Terminal 3:  roslaunch rosbridge_server rosbridge_websocket.launch
  (Optional)   rosrun dofbot_policy_bridge robot_controller.py
               (if not running, arm will still move via direct /policy/action)

Usage
─────
  # Replay episode 19 at recorded speed (default Jetson IP 192.168.0.8)
  conda run -n dofbot_controller python3 tools/replay_on_robot.py \\
      dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000019.hdf5

  # Slower playback (half speed), different Jetson IP
  conda run -n dofbot_controller python3 tools/replay_on_robot.py \\
      dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000019.hdf5 \\
      --speed 0.5 --jetson_ip 192.168.0.8

  # Go back to home position after replay
  conda run -n dofbot_controller python3 tools/replay_on_robot.py \\
      dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000019.hdf5 \\
      --home_after

Safety
──────
  • The script publishes through robot_controller.py which applies safety
    limits on the Jetson side.
  • Use --speed 0.3 for a first run so arm motion is slow.
  • Keep a hand near the power switch.
  • Press Ctrl+C to abort at any time; the script sends a "stop" command
    before disconnecting.
"""

import argparse
import math
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import roslibpy

# ── Coordinate conversions (copied from lerobot_inference_server.py) ──────────

NUM_JOINTS             = 6
RAD2DEG                = 180.0 / math.pi
GRIPPER_MIN_DEG        = 30.0
GRIPPER_MAX_DEG        = 180.0
GRIPPER_STATE_MIN_DEG  = 0.0
GRIPPER_STATE_MAX_DEG  = 90.0

POLICY_ACTION_TOPIC    = "/policy/action"
ROBOT_CMD_TOPIC        = "/robot/cmd"
ROBOT_READY_TOPIC      = "/robot/ready"
ACTION_MSG_TYPE        = "dofbot_pro_info/ArmJoint"
STRING_TYPE            = "std_msgs/String"
BOOL_TYPE              = "std_msgs/Bool"


def action_rad_to_deg(
    joints_rad: np.ndarray,
    gripper_max_deg: float,
    gripper_margin_deg: float,
) -> list[float]:
    """Convert stored action (radians) → servo degree commands (same as inference server)."""
    deg = []
    for i, r in enumerate(joints_rad):
        if i < 5:
            d = float(r) * RAD2DEG + 90.0
        else:
            # action[5] uses the gripper-state convention from /joint_states:
            # interp from state range [0°,90°] back to servo range [30°,180°].
            d_state = float(r) * RAD2DEG + 90.0
            d = float(np.interp(
                d_state,
                [GRIPPER_STATE_MIN_DEG, GRIPPER_STATE_MAX_DEG],
                [GRIPPER_MIN_DEG, GRIPPER_MAX_DEG],
            ))
        deg.append(float(np.clip(d, 0.0, 270.0)))
    # Optional replay-side soft clamp for gripper close direction.
    effective_gripper_max = max(GRIPPER_MIN_DEG, gripper_max_deg - gripper_margin_deg)
    deg[5] = float(np.clip(deg[5], GRIPPER_MIN_DEG, effective_gripper_max))
    return deg


# ── HDF5 loader ───────────────────────────────────────────────────────────────

def load_episode(hdf5_path: Path) -> dict:
    with h5py.File(hdf5_path, "r") as f:
        actions     = f["action"][()]           # (T, 6) float32 radians
        states      = f["observation/state"][()] # (T, 6) for reference
        fps         = float(f.attrs.get("fps", 5.0))
        ep_idx      = int(f.attrs.get("episode_index", -1))
        num_frames  = int(f.attrs.get("num_frames", actions.shape[0]))
        task_raw    = f.attrs.get("task", "")
        task        = task_raw.decode() if isinstance(task_raw, bytes) else str(task_raw)
    return dict(actions=actions, states=states, fps=fps,
                episode_index=ep_idx, num_frames=num_frames, task=task)


# ── Replay ────────────────────────────────────────────────────────────────────

def replay(args: argparse.Namespace) -> None:
    hdf5_path = Path(args.hdf5_path).resolve()
    if not hdf5_path.exists():
        print(f"Error: file not found: {hdf5_path}", file=sys.stderr)
        sys.exit(1)

    ep = load_episode(hdf5_path)
    fps = ep["fps"] * args.speed
    frame_interval = 1.0 / fps
    # move_time: how long the servo takes to reach the target (ms)
    # Set to slightly less than one frame so motion is continuous
    move_time_ms = int((frame_interval * 0.9) * 1000)

    T = ep["num_frames"]

    print(f"\nEpisode {ep['episode_index']:04d}  |  {T} frames  "
          f"|  recorded @ {ep['fps']:.1f} fps  |  replay @ {fps:.1f} fps")
    print(f"Task: {ep['task'] or '(none)'}")
    print(f"Move time per step: {move_time_ms} ms\n")

    # ── Connect to rosbridge ──────────────────────────────────────────────────
    print(f"Connecting to rosbridge at ws://{args.jetson_ip}:{args.jetson_port} …")
    client = roslibpy.Ros(host=args.jetson_ip, port=args.jetson_port)
    client.run()

    deadline = time.time() + 15.0
    while not client.is_connected and time.time() < deadline:
        time.sleep(0.2)
    if not client.is_connected:
        print(f"Error: could not connect to rosbridge at "
              f"{args.jetson_ip}:{args.jetson_port}.\n"
              "Check: roslaunch rosbridge_server rosbridge_websocket.launch",
              file=sys.stderr)
        sys.exit(1)
    print("Connected.\n")

    # ── Publishers ────────────────────────────────────────────────────────────
    action_pub = roslibpy.Topic(client, POLICY_ACTION_TOPIC, ACTION_MSG_TYPE)
    action_pub.advertise()

    cmd_pub = roslibpy.Topic(client, ROBOT_CMD_TOPIC, STRING_TYPE)
    cmd_pub.advertise()

    # ── Robot-ready flag (optimistic default: True if controller not running) ─
    robot_ready = {"value": True}

    def _cb_ready(msg):
        robot_ready["value"] = bool(msg.get("data", True))

    ready_sub = roslibpy.Topic(client, ROBOT_READY_TOPIC, BOOL_TYPE)
    ready_sub.subscribe(_cb_ready)

    time.sleep(1.0)  # let rosbridge register subscriptions

    def send_cmd(cmd: str):
        cmd_pub.publish(roslibpy.Message({"data": cmd}))
        print(f"[cmd] {cmd}")

    def publish_action(deg_cmds: list[float]):
        action_pub.publish(roslibpy.Message({
            "id":       0,
            "run_time": move_time_ms,
            "angle":    0.0,
            "joints":   deg_cmds,
        }))

    # ── Replay loop ───────────────────────────────────────────────────────────
    try:
        send_cmd("start")
        time.sleep(0.3)

        print("Starting replay — press Ctrl+C to abort.\n")
        print(f"{'Frame':>6}  {'Joints (deg)':>60}  Elapsed")
        print("-" * 80)

        t0 = time.time()
        for t in range(T):
            step_start = time.time()

            # Wait for the arm to settle before the next command (skip on
            # first step so we don't hang indefinitely if controller is absent)
            if t > 0 and args.wait_for_ready:
                wait_deadline = step_start + frame_interval * 2
                while not robot_ready["value"] and time.time() < wait_deadline:
                    time.sleep(0.01)

            deg = action_rad_to_deg(
                ep["actions"][t],
                gripper_max_deg=args.gripper_max_deg,
                gripper_margin_deg=args.gripper_margin_deg,
            )
            publish_action(deg)

            elapsed = time.time() - t0
            deg_str = "  ".join(f"{d:6.1f}" for d in deg)
            print(f"{t:6d}  {deg_str}  {elapsed:6.1f}s")

            # Sleep the remainder of the frame interval
            sleep_time = frame_interval - (time.time() - step_start)
            if sleep_time > 0:
                time.sleep(sleep_time)

        print(f"\nReplay complete ({T} frames).")

        if args.home_after:
            time.sleep(0.5)
            send_cmd("home")
            print("Sent home command.")

    except KeyboardInterrupt:
        print("\nAborted by user.")
        send_cmd("stop")

    finally:
        time.sleep(0.5)
        ready_sub.unsubscribe()
        action_pub.unadvertise()
        cmd_pub.unadvertise()
        client.terminate()
        print("Disconnected.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay a DofBot HDF5 episode on the real robot via rosbridge.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("hdf5_path",
                        help="Path to episode_XXXXXX.hdf5")
    parser.add_argument("--jetson_ip",   default="192.168.0.8",
                        help="IP address of the Jetson running rosbridge")
    parser.add_argument("--jetson_port", default=9090, type=int,
                        help="rosbridge WebSocket port")
    parser.add_argument("--speed",       default=1.0, type=float,
                        help="Playback speed multiplier (0.5 = half speed, 2.0 = double)")
    parser.add_argument("--home_after",  action="store_true",
                        help="Send 'home' command after replay completes")
    parser.add_argument("--wait_for_ready", action="store_true",
                        help="Wait for /robot/ready before each frame (requires robot_controller.py)")
    parser.add_argument("--gripper_max_deg", default=125.0, type=float,
                        help="Soft maximum close angle for gripper servo (deg, lower = less force)")
    parser.add_argument("--gripper_margin_deg", default=2.0, type=float,
                        help="Safety margin subtracted from --gripper_max_deg to avoid hard-stop chatter")
    return parser.parse_args()


if __name__ == "__main__":
    replay(parse_args())
