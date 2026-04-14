#!/usr/bin/env python3
"""
lerobot_inference_server.py — runs on the lab computer.

Mirrors the architecture of inference_server.py (the existing SRE-RL server)
but drives a LeRobot-compatible policy (ACT, Diffusion Policy, pi0, etc.)
instead of the custom SRE-RL pipeline.

No ROS installation required on this machine — communication with the Jetson
is handled entirely through roslibpy over the rosbridge WebSocket.

Architecture
────────────
  Jetson                              Lab Computer
  ──────                              ────────────
  roscore
  rosbridge_websocket  ←─ WS ──────→  lerobot_inference_server.py
  arm_driver.py  ←── TargetAngle ──   │  (this file)
  /joint_states  ──────────────────→  │  • subscribes to /joint_states
  /camera/color/image_raw  ────────→  │  • subscribes to /camera/color/image_raw
                                      │  • runs policy inference
                           TargetAngle  • publishes joint commands back

Startup (matches roslibpy_commands.md)
──────────────────────────────────────
  # Jetson terminal 1
  roscore

  # Jetson terminal 2
  roslaunch rosbridge_server rosbridge_websocket.launch

  # Jetson terminal 3
  rosrun dofbot_pro_info arm_driver.py

  # Jetson terminal 4 (optional but recommended)
  roslaunch orbbec_camera dabai_dcw2.launch

  # Lab computer — pick one policy_type:

  # mock: no ML, validates full pipeline (safe first step)
  python lerobot_inference_server.py --policy_type mock --inference_hz 0.2 --move_time_ms 2000

  # pretrained: HuggingFace checkpoint, no training needed
  python lerobot_inference_server.py --policy_type pretrained \
      --pretrained_repo lerobot/act_koch_real --inference_hz 10

  # local ACT checkpoint (after fine-tuning)
  python lerobot_inference_server.py --policy_type act \
      --checkpoint_path /path/to/checkpoint --inference_hz 10

Policy type progression
───────────────────────
  1. mock        – canned waypoints, confirms ROS ↔ lab wiring works
  2. pretrained  – HuggingFace checkpoint, confirms inference + joint mapping
  3. act         – your fine-tuned local checkpoint
  4. diffusion   – Diffusion Policy local checkpoint
"""

import argparse
import base64
import math
import threading
import time
from typing import Optional

import cv2
import numpy as np
import roslibpy

# ── Constants ─────────────────────────────────────────────────────────────────

NUM_JOINTS   = 6
RAD2DEG      = 180.0 / math.pi
DEG2RAD      = math.pi / 180.0

# Servo degree range for the gripper
GRIPPER_MIN_DEG       = 30.0
GRIPPER_MAX_DEG       = 180.0
# joint_states range for the gripper (after arm_driver normalisation)
GRIPPER_STATE_MIN_DEG = 0.0
GRIPPER_STATE_MAX_DEG = 90.0

JOINT_NAMES = [
    "Arm1_Joint", "Arm2_Joint", "Arm3_Joint",
    "Arm4_Joint", "Arm5_Joint", "grip_joint",
]

# ROS topic names
JOINT_STATE_TOPIC   = "joint_states"
IMAGE_TOPIC         = "/camera/color/image_raw"

# Publish to /policy/action so robot_controller.py on the Jetson can
# safety-check and sync motion before forwarding to arm_driver.py.
# Set to "TargetAngle" to bypass the controller (direct mode, no safety gate).
POLICY_ACTION_TOPIC = "/policy/action"

# robot_controller.py publishes True here when the arm has settled at its
# last target — used to synchronise inference rate with actual motion.
ROBOT_READY_TOPIC   = "/robot/ready"

# Episode control — publish "start"/"stop"/"home"/"reset" here
ROBOT_CMD_TOPIC     = "/robot/cmd"

JOINT_STATE_TYPE    = "sensor_msgs/JointState"
IMAGE_TYPE          = "sensor_msgs/Image"
ACTION_MSG_TYPE     = "dofbot_pro_info/ArmJoint"    # from yahboomcar_msgs
BOOL_TYPE           = "std_msgs/Bool"
STRING_TYPE         = "std_msgs/String"


# ── Coordinate conversions ─────────────────────────────────────────────────────

def joint_state_rad_to_deg(joints_rad) -> list:
    """
    Convert /joint_states positions (radians, offset from 90°) back to
    the servo degree commands expected by arm_driver.py.

    arm_driver convention:
        joint_state_rad  = (servo_deg - 90) * pi/180     for joints 0-4
        grip_state_deg   = interp(servo_deg, [30,180], [0,90])
        joint_state_rad  = (grip_state_deg - 90) * pi/180  for joint 5
    """
    deg = []
    for i, r in enumerate(joints_rad):
        if i < 5:
            d = r * RAD2DEG + 90.0
        else:
            # Undo the offset, then reverse the interp
            d_state = r * RAD2DEG + 90.0
            d = float(np.interp(d_state,
                                [GRIPPER_STATE_MIN_DEG, GRIPPER_STATE_MAX_DEG],
                                [GRIPPER_MIN_DEG, GRIPPER_MAX_DEG]))
        deg.append(float(np.clip(d, 0.0, 270.0)))
    return deg


def policy_action_to_deg(action: np.ndarray) -> list:
    """
    Convert a LeRobot policy output (6,) radians array → servo degree commands.
    LeRobot uses the same radians convention as /joint_states.
    """
    return joint_state_rad_to_deg(list(action.flatten()[:NUM_JOINTS]))


# ── Image decode (matches inference_server.py) ────────────────────────────────

def ros_image_to_cv2(img_msg: dict) -> np.ndarray:
    """Decode a rosbridge sensor_msgs/Image dict → OpenCV BGR uint8 array."""
    h        = img_msg["height"]
    w        = img_msg["width"]
    encoding = img_msg["encoding"]
    data     = img_msg["data"]

    if isinstance(data, str):
        raw = base64.b64decode(data)
    elif isinstance(data, list):
        raw = bytes(data)
    else:
        raise ValueError(f"Unsupported image data type: {type(data)}")

    if encoding in ("bgr8", "rgb8"):
        img = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3).copy()
        if encoding == "rgb8":
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif encoding in ("mono8", "8UC1"):
        img = np.frombuffer(raw, dtype=np.uint8).reshape(h, w).copy()
    else:
        raise ValueError(f"Unsupported image encoding: {encoding}")

    return img  # BGR uint8


# ── Policy classes ─────────────────────────────────────────────────────────────

class MockPolicy:
    """
    No ML required. Cycles through safe waypoints (near home, ±10° per joint)
    to confirm the full Jetson ↔ lab ↔ servo pipeline is wired correctly.

    Run with --inference_hz 0.2 --move_time_ms 2000 so movements are slow.
    """
    _WAYPOINTS = [
        [90.0,  90.0,  90.0,  0.0,  90.0,  30.0],   # home
        [100.0, 90.0,  90.0,  0.0,  90.0,  30.0],   # Arm1 +10°
        [90.0, 100.0,  90.0,  0.0,  90.0,  30.0],   # Arm2 +10°
        [90.0,  90.0, 100.0,  0.0,  90.0,  30.0],   # Arm3 +10°
        [90.0,  90.0,  90.0, 10.0,  90.0,  30.0],   # Arm4 +10°
        [90.0,  90.0,  90.0,  0.0, 100.0,  30.0],   # Arm5 +10°
        [90.0,  90.0,  90.0,  0.0,  90.0, 100.0],   # gripper close
        [90.0,  90.0,  90.0,  0.0,  90.0,  30.0],   # home (gripper open)
        [90.0,  140.0,  90.0,  0.0,  90.0,  30.0],   # 
    ]

    def __init__(self):
        self._step = 0
        print(f"[MockPolicy] Loaded — {len(self._WAYPOINTS)} waypoints")

    def predict(self, obs: dict) -> np.ndarray:
        deg = self._WAYPOINTS[self._step % len(self._WAYPOINTS)]
        print(f"[MockPolicy] Waypoint {self._step % len(self._WAYPOINTS)}: {deg} deg")
        self._step += 1
        # Convert to radians (same convention as /joint_states)
        rad = [(d - 90.0) * DEG2RAD for d in deg[:5]]
        grip_state = float(np.interp(deg[5],
                                     [GRIPPER_MIN_DEG, GRIPPER_MAX_DEG],
                                     [GRIPPER_STATE_MIN_DEG, GRIPPER_STATE_MAX_DEG]))
        rad.append((grip_state - 90.0) * DEG2RAD)
        return np.array(rad, dtype=np.float32)


class PretrainedLeRobotPolicy:
    """
    Load any LeRobot checkpoint from HuggingFace Hub.

    Good starting checkpoints for a 6-DOF tabletop arm:
        lerobot/act_koch_real      – ACT on Koch v1.1 (closest hardware match)
        lerobot/act_aloha_sim_transfer_cube_human

    pip install lerobot
    """
    def __init__(self, repo_id: str, device: str = "cpu"):
        from lerobot.common.policies.factory import make_policy_from_pretrained
        import torch
        self.device = device
        self.policy = make_policy_from_pretrained(repo_id)
        self.policy = self.policy.to(device)
        self.policy.eval()
        print(f"[PretrainedPolicy] Loaded: {repo_id} on {device}")

    def predict(self, obs: dict) -> np.ndarray:
        import torch
        image = torch.from_numpy(obs["image"]).float().unsqueeze(0).to(self.device)
        state = torch.from_numpy(obs["state"]).float().unsqueeze(0).to(self.device)
        with torch.no_grad():
            action = self.policy.select_action({
                "observation.image": image,
                "observation.state": state,
            })
        a = action.cpu().numpy()
        # Handle chunked policies that return (1, T, 6) or (1, 6)
        if a.ndim == 3:
            a = a[0, 0]
        elif a.ndim == 2:
            a = a[0]
        return a.flatten()[:NUM_JOINTS].astype(np.float32)


class LocalACTPolicy:
    """
    Fine-tuned ACT checkpoint produced by train_act.py.

    Checkpoint layout (output of train_act.py):
        <checkpoint_dir>/model.pt      ← policy state dict
        <checkpoint_dir>/config.json   ← ACTConfig constructor kwargs
        <checkpoint_dir>/stats.json    ← dataset normalisation stats
    """
    def __init__(self, checkpoint_path: str, device: str = "cpu"):
        import json
        import torch
        from lerobot.common.policies.act.configuration_act import ACTConfig
        from lerobot.common.policies.act.modeling_act import ACTPolicy

        ckpt_dir = Path(checkpoint_path)

        with open(ckpt_dir / "config.json") as fh:
            config_dict = json.load(fh)

        with open(ckpt_dir / "stats.json") as fh:
            stats_raw = json.load(fh)
        dataset_stats = {
            feat: {k: torch.tensor(v) for k, v in vals.items()}
            for feat, vals in stats_raw.items()
        }

        config = ACTConfig(**config_dict)
        self.policy = ACTPolicy(config, dataset_stats=dataset_stats)
        self.policy.load_state_dict(
            torch.load(ckpt_dir / "model.pt", map_location=device,
                       weights_only=True)
        )
        self.policy = self.policy.to(device)
        self.policy.eval()
        self.device = device
        print(f"[ACTPolicy] Loaded from {checkpoint_path}")

    def predict(self, obs: dict) -> np.ndarray:
        import torch
        # obs["image"] is (C, H, W) float32 [0,1].
        # Policy expects (batch=1, n_obs_steps=1, C, H, W).
        image = torch.from_numpy(obs["image"]).float()
        image = image.unsqueeze(0).unsqueeze(0).to(self.device)   # (1, 1, C, H, W)
        state = torch.from_numpy(obs["state"]).float()
        state = state.unsqueeze(0).unsqueeze(0).to(self.device)   # (1, 1, 6)
        with torch.no_grad():
            action = self.policy.select_action({
                "observation.images.top": image,
                "observation.state":      state,
            })
        a = action.cpu().numpy()
        # select_action may return (1, chunk, 6), (1, 6), or (6,)
        if a.ndim == 3:
            a = a[0, 0]
        elif a.ndim == 2:
            a = a[0]
        return a.flatten()[:NUM_JOINTS].astype(np.float32)


class LocalDiffusionPolicy:
    """Fine-tuned Diffusion Policy checkpoint stored on disk."""
    def __init__(self, checkpoint_path: str, device: str = "cpu"):
        from lerobot.common.policies.diffusion.modeling_diffusion import DiffusionPolicy
        from lerobot.common.utils.utils import init_hydra_config
        import torch
        cfg = init_hydra_config(checkpoint_path)
        self.policy = DiffusionPolicy(cfg.policy)
        self.policy.load_state_dict(
            torch.load(f"{checkpoint_path}/model.pt", map_location=device)
        )
        self.policy.eval()
        self.device = device
        print(f"[DiffusionPolicy] Loaded from {checkpoint_path}")

    def predict(self, obs: dict) -> np.ndarray:
        import torch
        image = torch.from_numpy(obs["image"]).float().unsqueeze(0).to(self.device)
        state = torch.from_numpy(obs["state"]).float().unsqueeze(0).to(self.device)
        with torch.no_grad():
            action = self.policy.select_action({
                "observation.image": image,
                "observation.state": state,
            })
        a = action.cpu().numpy()
        if a.ndim == 3:
            a = a[0, 0]
        elif a.ndim == 2:
            a = a[0]
        return a.flatten()[:NUM_JOINTS].astype(np.float32)


# ── Main server ───────────────────────────────────────────────────────────────

class LeRobotInferenceServer:
    """
    Connects to rosbridge on the Jetson, subscribes to camera + joint state
    topics, runs LeRobot policy inference, and publishes joint commands back.

    This is a direct replacement for / companion to inference_server.py but
    for standard open robot policy models instead of the custom SRE-RL pipeline.
    """

    def __init__(self, args):
        self.args         = args
        self.img_size     = (args.image_height, args.image_width)
        self.inference_hz = args.inference_hz
        self.move_time_ms = args.move_time_ms

        self._lock              = threading.Lock()
        self._latest_image: Optional[np.ndarray] = None   # (H, W, 3) BGR uint8
        self._latest_state: Optional[np.ndarray] = None   # (6,) float32 radians
        self._image_stamp: float = 0.0
        self._state_stamp: float = 0.0
        self._inference_lock    = threading.Lock()

        # ── Load policy ───────────────────────────────────────────────────
        print(f"Loading policy: {args.policy_type} …")
        if args.policy_type == "mock":
            self.policy = MockPolicy()
        elif args.policy_type == "pretrained":
            self.policy = PretrainedLeRobotPolicy(args.pretrained_repo, args.device)
        elif args.policy_type == "act":
            self.policy = LocalACTPolicy(args.checkpoint_path, args.device)
        elif args.policy_type == "diffusion":
            self.policy = LocalDiffusionPolicy(args.checkpoint_path, args.device)
        else:
            raise ValueError(f"Unknown policy_type: {args.policy_type}. "
                             "Use: mock | pretrained | act | diffusion")
        print("Policy ready.")

        # ── Connect to rosbridge on Jetson ────────────────────────────────
        print(f"Connecting to rosbridge at ws://{args.jetson_ip}:{args.jetson_port} …")
        self.client = roslibpy.Ros(host=args.jetson_ip, port=args.jetson_port)
        self.client.run()

        deadline = time.time() + 15.0
        while not self.client.is_connected and time.time() < deadline:
            time.sleep(0.2)
        if not self.client.is_connected:
            raise RuntimeError(
                f"Could not connect to rosbridge at {args.jetson_ip}:{args.jetson_port}. "
                "Is roslaunch rosbridge_server rosbridge_websocket.launch running on the Jetson?"
            )
        print(f"Connected to Jetson rosbridge.")

        # ── Publisher: /policy/action → robot_controller.py (Jetson) ───────
        # robot_controller safety-checks the command then forwards to arm_driver.
        self._cmd_pub = roslibpy.Topic(
            self.client, POLICY_ACTION_TOPIC, ACTION_MSG_TYPE
        )
        self._cmd_pub.advertise()

        # Episode control publisher ("start" / "stop" / "home" / "reset")
        self._ctrl_pub = roslibpy.Topic(
            self.client, ROBOT_CMD_TOPIC, STRING_TYPE
        )
        self._ctrl_pub.advertise()

        # ── Subscribers ───────────────────────────────────────────────────
        self._image_sub = roslibpy.Topic(
            self.client, IMAGE_TOPIC, IMAGE_TYPE
        )
        self._image_sub.subscribe(self._cb_image)

        self._joint_sub = roslibpy.Topic(
            self.client, JOINT_STATE_TOPIC, JOINT_STATE_TYPE
        )
        self._joint_sub.subscribe(self._cb_joint_states)

        # /robot/ready — True when arm has settled; used to gate inference rate
        self._robot_ready = True   # optimistic default (works without controller)
        self._ready_sub = roslibpy.Topic(
            self.client, ROBOT_READY_TOPIC, BOOL_TYPE
        )
        self._ready_sub.subscribe(self._cb_robot_ready)

        # Give rosbridge time to register subscriptions on the Jetson side
        print("Waiting for rosbridge subscription handshake…")
        time.sleep(2.0)
        print(f"Subscribed to {IMAGE_TOPIC} and {JOINT_STATE_TOPIC}")
        print(f"Publishing to  {POLICY_ACTION_TOPIC}")
        print(f"Running at {self.inference_hz} Hz — move_time={self.move_time_ms} ms")
        print(f"Episode control: publish to {ROBOT_CMD_TOPIC} ('start'/'stop'/'home'/'reset')")
        if args.policy_type == "mock":
            print("[MockPolicy] Arm will step through safe waypoints. "
                  "Keep hand near power switch.")

    # ── Callbacks (roslibpy WebSocket thread — keep fast) ─────────────────────

    def _cb_robot_ready(self, msg: dict):
        self._robot_ready = bool(msg.get("data", True))

    def _cb_image(self, msg: dict):
        try:
            bgr = ros_image_to_cv2(msg)
            bgr = cv2.resize(bgr, (self.img_size[1], self.img_size[0]))
            with self._lock:
                self._latest_image = bgr
                self._image_stamp  = time.time()
        except Exception as e:
            print(f"[ImageCallback] Error: {e}")

    def _cb_joint_states(self, msg: dict):
        try:
            names    = msg.get("name", [])
            positions = msg.get("position", [])
            name_to_idx = {n: i for i, n in enumerate(names)}
            state = np.zeros(NUM_JOINTS, dtype=np.float32)
            for k, jname in enumerate(JOINT_NAMES):
                if jname in name_to_idx:
                    state[k] = float(positions[name_to_idx[jname]])
            with self._lock:
                self._latest_state = state
                self._state_stamp  = time.time()
        except Exception as e:
            print(f"[JointStateCallback] Error: {e}")

    # ── Inference loop ─────────────────────────────────────────────────────────

    def _observations_ready(self) -> bool:
        max_age = 1.0  # seconds
        now = time.time()
        return (
            self._latest_image is not None and
            self._latest_state is not None and
            (now - self._image_stamp) < max_age and
            (now - self._state_stamp) < max_age
        )

    def _build_obs(self) -> dict:
        bgr = self._latest_image.copy()
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        # (3, H, W) float32 normalised to [0, 1]
        image_chw = np.transpose(rgb, (2, 0, 1)).astype(np.float32) / 255.0
        return {
            "image": image_chw,
            "state": self._latest_state.copy(),
        }

    def send_episode_cmd(self, cmd: str):
        """Send an episode control command to robot_controller.py on the Jetson."""
        self._ctrl_pub.publish(roslibpy.Message({"data": cmd}))
        print(f"[Server] Sent episode command: {cmd}")

    def _run_inference_step(self):
        """Called at inference_hz. Thread-safe: drops frame if already busy."""
        if not self._inference_lock.acquire(blocking=False):
            print("[Server] Busy — dropping frame.")
            return

        try:
            # Wait for the arm to settle before the next inference step.
            # Falls through immediately if robot_controller is not running
            # (self._robot_ready stays True by default).
            if not self._robot_ready:
                print("[Server] Arm not settled yet — waiting…")
                return

            with self._lock:
                ready = self._observations_ready()
                obs   = self._build_obs() if ready else None

            if not ready:
                print("[Server] Waiting for observations "
                      f"(image={'yes' if self._latest_image is not None else 'no'}, "
                      f"state={'yes' if self._latest_state is not None else 'no'})…")
                return

            t0 = time.time()
            action = self.policy.predict(obs)   # (6,) radians
            dt_ms  = (time.time() - t0) * 1000.0

            deg_cmds = policy_action_to_deg(action)
            print(f"[Server] Inference {dt_ms:.1f} ms  →  {[f'{d:.1f}' for d in deg_cmds]} deg")
            self._publish_action(deg_cmds)

        except Exception as e:
            import traceback
            print(f"[Server] Inference error:\n{traceback.format_exc()}")
        finally:
            self._inference_lock.release()

    def _publish_action(self, deg_commands: list):
        """
        Publish to TargetAngle (dofbot_pro_info/ArmJoint).
        arm_driver.py checks len(msg.joints) != 0 to distinguish bulk vs single.
        """
        msg = {
            "id":       0,
            "run_time": self.move_time_ms,
            "angle":    0.0,
            "joints":   [float(d) for d in deg_commands],
        }
        self._cmd_pub.publish(roslibpy.Message(msg))

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def spin(self):
        interval = 1.0 / self.inference_hz
        print("[Server] Running. Ctrl+C to stop.")
        try:
            while self.client.is_connected:
                self._run_inference_step()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[Server] Shutting down…")
        finally:
            self._image_sub.unsubscribe()
            self._joint_sub.unsubscribe()
            self._cmd_pub.unadvertise()
            self.client.terminate()
            print("[Server] Done.")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="LeRobot inference server — runs on the lab computer, "
                    "connects to Jetson via roslibpy/rosbridge.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Policy selection
    parser.add_argument(
        "--policy_type",
        choices=["mock", "pretrained", "act", "diffusion"],
        default="mock",
        help="mock=safe waypoints (no ML) | pretrained=HuggingFace | "
             "act=local ACT checkpoint | diffusion=local Diffusion checkpoint",
    )
    parser.add_argument(
        "--pretrained_repo",
        default="lerobot/act_aloha_sim_transfer_cube_human",
        help="HuggingFace repo id for pretrained mode",
    )
    parser.add_argument(
        "--checkpoint_path",
        default="",
        help="Local LeRobot checkpoint directory for act/diffusion modes",
    )

    # Jetson connection
    parser.add_argument("--jetson_ip",   default="192.168.0.8",  type=str)
    parser.add_argument("--jetson_port", default=9090,           type=int)

    # Control parameters
    parser.add_argument("--inference_hz",  default=10.0,  type=float,
                        help="Policy query rate in Hz (use 0.2 for mock mode)")
    parser.add_argument("--move_time_ms",  default=200,   type=int,
                        help="Servo move duration in ms (use ≥1000 for mock)")
    parser.add_argument("--image_height",  default=224,   type=int)
    parser.add_argument("--image_width",   default=224,   type=int)

    # Compute
    parser.add_argument("--device", default="cpu", type=str,
                        help="cpu | cuda:0 | mps")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Auto-detect MPS (Apple Silicon) if device not explicitly set
    if args.device == "cpu":
        try:
            import torch
            if torch.backends.mps.is_available():
                args.device = "mps"
                print("[Server] Apple MPS detected — using GPU acceleration.")
        except ImportError:
            pass

    server = LeRobotInferenceServer(args)
    server.spin()
