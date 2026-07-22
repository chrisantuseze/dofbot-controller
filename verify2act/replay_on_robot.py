#!/usr/bin/env python3
"""
verify2act/replay_on_robot.py
=============================
Replays a recorded Dofbot Pro HDF5 episode on the physical robot by streaming
the stored joint-angle actions over a roslibpy WebSocket connection to the
Jetson's rosbridge server.

Commands are published to /policy/action (ArmJoint), which flows through
robot_controller.py's safety gate before reaching arm_driver.py — identical to
the live inference path.

Prerequisites (Jetson terminals, in order)
------------------------------------------
  Terminal 1:  roscore
  Terminal 2:  rosrun dofbot_pro_info arm_driver.py
  Terminal 3:  roslaunch rosbridge_server rosbridge_websocket.launch
  Terminal 4:  rosrun dofbot_policy_bridge robot_controller.py _gripper_soft_max_deg:=120
  Terminal 5:  rostopic pub -1 /robot/cmd std_msgs/String "data: 'start'"

Usage
-----
    # Safety test at half speed — always do this first on a new episode
    python3 verify2act/replay_on_robot.py \\
        dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000019.hdf5 \\
        --speed 0.5 --home_after --jetson_ip 192.168.0.8

    # Video take — synchronized, tuned gripper limits
    python3 verify2act/replay_on_robot.py \\
        dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000019.hdf5 \\
        --speed 0.4 --wait_for_ready \\
        --gripper_max_deg 118 --gripper_margin_deg 2 \\
        --home_after --jetson_ip 192.168.0.8
"""

import argparse
import math
import sys
import threading
import time
from pathlib import Path

import h5py
import numpy as np

try:
    import roslibpy
except ImportError:
    print("ERROR: roslibpy not installed. Run: pip install roslibpy", file=sys.stderr)
    sys.exit(1)

# ── Constants (match robot_controller.py) ─────────────────────────────────────
JOINTS_HOME    = [90.0, 90.0, 90.0, 0.0, 90.0, 30.0]
NUM_JOINTS     = 6
RAD2DEG        = 180.0 / math.pi

JOINT_SAFE_MIN = [  0.0,  30.0,   0.0,   0.0,   0.0,  30.0]
JOINT_SAFE_MAX = [180.0, 270.0, 180.0, 270.0, 180.0, 180.0]

DEFAULT_JETSON_IP   = "192.168.0.8"
DEFAULT_BRIDGE_PORT = 9090
READY_TIMEOUT_S     = 15.0   # seconds to wait for /robot/ready


# ── Action decoding ───────────────────────────────────────────────────────────

def action_rad_to_deg(joints_rad: np.ndarray) -> list:
    """
    Convert stored HDF5 radians back to servo-degree commands.

    data_collector.py storage convention:
      joints 0-4:  rad = (servo_deg - 90) * pi/180
      joint  5:    grip_state_deg = interp(servo_deg, [30,180]->[0,90])
                   rad = (grip_state_deg - 90) * pi/180
    """
    deg = joints_rad * RAD2DEG + 90.0                            # joints 0-4
    grip_state = float(joints_rad[5]) * RAD2DEG + 90.0
    deg[5]     = float(np.interp(grip_state, [0.0, 90.0], [30.0, 180.0]))
    return deg.tolist()


def clamp_joints(joints: list,
                 gripper_max_deg: float,
                 gripper_margin_deg: float) -> list:
    """Clamp to safe limits and apply gripper soft-close override."""
    clamped = [
        float(np.clip(j, JOINT_SAFE_MIN[i], JOINT_SAFE_MAX[i]))
        for i, j in enumerate(joints)
    ]
    # Soft gripper ceiling
    effective_max = gripper_max_deg - gripper_margin_deg
    clamped[5] = float(np.clip(clamped[5], JOINT_SAFE_MIN[5], effective_max))
    return clamped


# ── Robot interface ───────────────────────────────────────────────────────────

class RobotInterface:
    """
    Thin roslibpy wrapper for sending joint commands to the Jetson.
    """

    def __init__(self, jetson_ip: str, port: int = DEFAULT_BRIDGE_PORT):
        self.host = jetson_ip
        self.port = port
        self._client = roslibpy.Ros(host=jetson_ip, port=port)
        self._ready_event  = threading.Event()
        self._ready_value  = False
        self._ready_lock   = threading.Lock()

        self._action_pub = None
        self._cmd_pub    = None
        self._ready_sub  = None

    def connect(self, timeout: float = 10.0) -> None:
        """Open the WebSocket connection and wait until it's live."""
        self._client.run()

        deadline = time.time() + timeout
        while not self._client.is_connected and time.time() < deadline:
            time.sleep(0.1)

        if not self._client.is_connected:
            raise ConnectionError(
                f"Could not connect to rosbridge at "
                f"{self.host}:{self.port} within {timeout}s"
            )

        print(f"[RobotInterface] Connected to rosbridge @ "
              f"{self.host}:{self.port}")

        # Publishers
        self._action_pub = roslibpy.Topic(
            self._client, "/policy/action", "dofbot_pro_info/ArmJoint")
        self._cmd_pub = roslibpy.Topic(
            self._client, "/robot/cmd", "std_msgs/String")

        # /robot/ready subscriber
        self._ready_sub = roslibpy.Topic(
            self._client, "/robot/ready", "std_msgs/Bool")
        self._ready_sub.subscribe(self._on_ready)

    def _on_ready(self, msg: dict) -> None:
        is_ready = bool(msg.get("data", False))
        with self._ready_lock:
            self._ready_value = is_ready
        if is_ready:
            self._ready_event.set()

    def send_joints(self, joints_deg: list, move_time_ms: int) -> None:
        """Publish an ArmJoint command to /policy/action."""
        if self._action_pub is None:
            raise RuntimeError("Not connected. Call connect() first.")
        msg = roslibpy.Message({
            "joints":   [float(j) for j in joints_deg],
            "run_time": int(move_time_ms),
        })
        self._action_pub.publish(msg)

    def wait_for_ready(self, timeout: float = READY_TIMEOUT_S) -> bool:
        """Block until /robot/ready is True. Returns True if settled, False on timeout."""
        self._ready_event.clear()
        # If already ready, return immediately
        with self._ready_lock:
            if self._ready_value:
                return True
        return self._ready_event.wait(timeout=timeout)

    def go_home(self, move_time_ms: int = 3000) -> None:
        """Send the robot to its home position."""
        print("[RobotInterface] Returning to home position...")
        self.send_joints(JOINTS_HOME, move_time_ms)
        time.sleep(move_time_ms / 1000.0 + 0.5)

    def send_cmd(self, cmd: str) -> None:
        """Publish to /robot/cmd (e.g. 'start', 'stop', 'home')."""
        if self._cmd_pub is None:
            raise RuntimeError("Not connected. Call connect() first.")
        self._cmd_pub.publish(roslibpy.Message({"data": cmd}))

    def disconnect(self) -> None:
        if self._ready_sub:
            self._ready_sub.unsubscribe()
        if self._client.is_connected:
            self._client.terminate()
        print("[RobotInterface] Disconnected.")


# ── Replay engine ─────────────────────────────────────────────────────────────

def replay_episode(hdf5_path: Path,
                   robot: RobotInterface,
                   speed: float,
                   wait_for_ready: bool,
                   gripper_max_deg: float,
                   gripper_margin_deg: float,
                   base_move_time_ms: int) -> None:
    """
    Stream every action in the episode to the robot.

    Args:
        hdf5_path:         Path to the HDF5 episode file.
        robot:             Connected RobotInterface.
        speed:             Time scaling (0.5 = double the move_time, i.e. half speed).
                           Values < 1.0 are slower (safer). Values > 1.0 are faster.
        wait_for_ready:    If True, block between steps until /robot/ready is True.
        gripper_max_deg:   Soft ceiling for the gripper servo (deg).
        gripper_margin_deg:Extra safety margin subtracted from gripper_max_deg.
        base_move_time_ms: Base move-time per step when not waiting for ready.
    """
    with h5py.File(hdf5_path, "r") as f:
        fps         = float(f.attrs.get("fps", 10))
        task_raw    = f.attrs.get("task", "")
        task        = task_raw.decode() if isinstance(task_raw, bytes) else str(task_raw)
        actions     = f["action"][()]           # (T, 6) float32 rad

    T = actions.shape[0]
    # move_time = duration each servo move should take
    # In replay we scale the original recording fps to get per-step timing
    step_duration_ms = int((1000.0 / fps) / speed)

    print(f"\n[Replay] Episode: {hdf5_path.name}")
    print(f"[Replay] Task:    {task or '(no label)'}")
    print(f"[Replay] Frames:  {T}  |  recorded fps: {fps:.1f}  "
          f"|  speed: {speed:.2f}x  |  step_ms: {step_duration_ms}")
    print(f"[Replay] Gripper max: {gripper_max_deg - gripper_margin_deg:.1f} deg "
          f"(max={gripper_max_deg}, margin={gripper_margin_deg})")
    print(f"[Replay] wait_for_ready: {wait_for_ready}\n")

    input("Press ENTER to start replay (make sure the robot is clear)... ")

    t_start = time.time()
    for t in range(T):
        raw_deg    = action_rad_to_deg(actions[t].copy())
        joints_deg = clamp_joints(raw_deg, gripper_max_deg, gripper_margin_deg)

        robot.send_joints(joints_deg, move_time_ms=step_duration_ms)

        if t % 10 == 0 or t == T - 1:
            print(f"  step {t+1:04d}/{T:04d}  "
                  f"joints: {[f'{j:.1f}' for j in joints_deg]}")

        if wait_for_ready:
            settled = robot.wait_for_ready(timeout=READY_TIMEOUT_S)
            if not settled:
                print(f"  WARNING: /robot/ready timed out at step {t+1} — continuing.")
        else:
            time.sleep(step_duration_ms / 1000.0)

    elapsed = time.time() - t_start
    print(f"\n[Replay] Done — {T} steps in {elapsed:.1f}s")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Replay a Dofbot Pro HDF5 episode on the physical robot.")

    parser.add_argument("episode",
                        help="Path to the episode .hdf5 file to replay.")
    parser.add_argument("--jetson_ip", default=DEFAULT_JETSON_IP,
                        help=f"Jetson IP address (default: {DEFAULT_JETSON_IP})")
    parser.add_argument("--port", type=int, default=DEFAULT_BRIDGE_PORT,
                        help=f"rosbridge WebSocket port (default: {DEFAULT_BRIDGE_PORT})")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Speed scaling: 0.5 = half speed (safer), 1.0 = recorded speed. "
                             "Values < 1 give longer move_time_ms (default: 1.0)")
    parser.add_argument("--wait_for_ready", action="store_true",
                        help="Block between steps until /robot/ready is True "
                             "(synchronized replay — recommended for video takes).")
    parser.add_argument("--home_after", action="store_true",
                        help="Move the robot to home position after the episode.")
    parser.add_argument("--gripper_max_deg", type=float, default=140.0,
                        help="Soft ceiling for gripper servo degrees (default: 140.0). "
                             "Use 118 for delicate objects.")
    parser.add_argument("--gripper_margin_deg", type=float, default=0.0,
                        help="Extra safety margin subtracted from --gripper_max_deg "
                             "(default: 0.0). Use 2.0 for extra safety.")
    parser.add_argument("--move_time_ms", type=int, default=None,
                        help="Fixed move_time_ms per step — overrides speed-scaled fps timing. "
                             "Use for coarse timing control.")
    args = parser.parse_args()

    hdf5_path = Path(args.episode)
    if not hdf5_path.is_file():
        print(f"ERROR: episode file not found: {hdf5_path}", file=sys.stderr)
        sys.exit(1)

    robot = RobotInterface(jetson_ip=args.jetson_ip, port=args.port)

    try:
        robot.connect()

        # Ensure robot is in running state before replay
        print("[Replay] Sending 'start' to /robot/cmd ...")
        robot.send_cmd("start")
        time.sleep(0.5)

        replay_episode(
            hdf5_path       = hdf5_path,
            robot           = robot,
            speed           = args.speed,
            wait_for_ready  = args.wait_for_ready,
            gripper_max_deg = args.gripper_max_deg,
            gripper_margin_deg = args.gripper_margin_deg,
            base_move_time_ms  = args.move_time_ms or 200,
        )

        if args.home_after:
            robot.go_home()

    except KeyboardInterrupt:
        print("\n[Replay] Interrupted by user.")
        if args.home_after:
            try:
                robot.go_home()
            except Exception:
                pass
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
