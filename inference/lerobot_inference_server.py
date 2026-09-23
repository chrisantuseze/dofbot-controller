#!/usr/bin/env python3
"""
lerobot_inference_server.py
===========================
Live Real-Robot Inference Server for Language-Conditioned ACT Policy.

Subscribes to:
  - /camera/color/image_raw (sensor_msgs/Image)
  - joint_states            (sensor_msgs/JointState)
  - /policy/command         (std_msgs/String) — e.g. "pick green cube"
  - /robot/ready            (std_msgs/Bool)

Publishes to:
  - /policy/action          (dofbot_pro_info/ArmJoint)

Usage:
  # Run directly on Jetson or remote lab computer
  python3 inference/lerobot_inference_server.py \
      --checkpoint_dir runs/act_dofbot_001/checkpoints/step_003000 \
      --jetson_ip 127.0.0.1 \
      --inference_hz 10
"""

import argparse
import base64
import json
import math
import sys
import threading
import time
from pathlib import Path
from typing import Optional, List

import cv2
import numpy as np
import torch

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from training.dataset_utils import text_to_task_id, stats_from_json, STATE_KEY, ACTION_KEY, IMAGE_KEY
from inference.policy import LanguageACTPolicy

try:
    import roslibpy
except ImportError:
    print("ERROR: roslibpy not installed. Run: pip install roslibpy", file=sys.stderr)
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────
NUM_JOINTS = 6
RAD2DEG = 180.0 / math.pi
DEG2RAD = math.pi / 180.0

JOINT_SAFE_MIN = [  0.0,  30.0,   0.0,   0.0,   0.0,  30.0]
JOINT_SAFE_MAX = [180.0, 270.0, 180.0, 270.0, 180.0, 180.0]
JOINTS_HOME    = [ 90.0,  90.0,  90.0,   0.0,  90.0,  30.0]


def action_rad_to_deg(joints_rad: np.ndarray) -> list:
    """Convert stored policy radians to physical servo degrees."""
    deg = (joints_rad * RAD2DEG + 90.0).tolist()
    # Gripper joint 5 mapping:
    # rad = (grip_state_deg - 90) * pi / 180
    # grip_state_deg in [0, 90] -> physical servo in [30, 180]
    grip_state = float(joints_rad[5]) * RAD2DEG + 90.0
    deg[5] = float(np.interp(grip_state, [0.0, 90.0], [30.0, 180.0]))
    return deg


def joint_state_to_rad(joints_deg: list) -> np.ndarray:
    """Convert incoming servo / state degrees to policy input radians."""
    rad = (np.array(joints_deg, dtype=np.float32) - 90.0) * DEG2RAD
    return rad


def ros_image_to_cv2(img_msg: dict) -> np.ndarray:
    """Decode rosbridge sensor_msgs/Image message to cv2 image."""
    h = img_msg['height']
    w = img_msg['width']
    encoding = img_msg['encoding']
    data = img_msg['data']

    if isinstance(data, str):
        raw = base64.b64decode(data)
    elif isinstance(data, list):
        raw = bytes(data)
    else:
        raise ValueError(f"Unsupported image data type: {type(data)}")

    if encoding in ('bgr8', 'rgb8'):
        img = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3).copy()
        if encoding == 'bgr8':
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    elif encoding in ('mono8', '8UC1'):
        img = np.frombuffer(raw, dtype=np.uint8).reshape(h, w).copy()
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    else:
        img = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, -1)[:, :, :3].copy()
    return img


class DofBotInferenceServer:
    def __init__(self, args):
        self.args = args
        self.device = torch.device(args.device)

        # 1. Load Model Checkpoint & Config
        ckpt_dir = Path(args.checkpoint_dir)
        print(f"Loading checkpoint from {ckpt_dir}...")
        with open(ckpt_dir / "config.json", "r") as f:
            self.config = json.load(f)
        with open(ckpt_dir / "stats.json", "r") as f:
            self.stats = stats_from_json(json.load(f), device=self.device)

        self.policy = LanguageACTPolicy(
            chunk_size=self.config.get("chunk_size", 16),
            state_dim=self.config.get("state_dim", 6),
            action_dim=self.config.get("action_dim", 6),
            num_tasks=self.config.get("num_tasks", 16),
            dim_model=self.config.get("dim_model", 256),
            nhead=self.config.get("nhead", 4),
            num_encoder_layers=self.config.get("num_encoder_layers", 2),
            num_decoder_layers=self.config.get("num_decoder_layers", 2),
            dim_feedforward=self.config.get("dim_feedforward", 512),
            latent_dim=self.config.get("latent_dim", 32),
            use_vae=self.config.get("use_vae", True),
        ).to(self.device)

        model_path = ckpt_dir / "model.pt"
        self.policy.load_state_dict(torch.load(model_path, map_location=self.device))
        self.policy.eval()
        print("Policy weights successfully loaded.")

        # State storage
        self._lock = threading.Lock()
        self.latest_image: Optional[np.ndarray] = None
        self.latest_joints: Optional[list] = None
        self.current_command: str = args.default_command
        self.robot_ready: bool = True
        self.is_running_episode: bool = False

        # 2. Connect ROS Bridge
        print(f"Connecting to rosbridge at {args.jetson_ip}:{args.bridge_port}...")
        self.ros = roslibpy.Ros(host=args.jetson_ip, port=args.bridge_port)
        self.ros.run()
        print(f"Connected to ROS bridge: {self.ros.is_connected}")

        # Topics
        self.sub_img = roslibpy.Topic(self.ros, args.image_topic, "sensor_msgs/Image", throttle_rate=100)
        self.sub_img.subscribe(self._on_image)

        self.sub_joints = roslibpy.Topic(self.ros, "joint_states", "sensor_msgs/JointState")
        self.sub_joints.subscribe(self._on_joints)

        self.sub_ready = roslibpy.Topic(self.ros, "/robot/ready", "std_msgs/Bool")
        self.sub_ready.subscribe(self._on_ready)

        self.sub_cmd = roslibpy.Topic(self.ros, "/policy/command", "std_msgs/String")
        self.sub_cmd.subscribe(self._on_command)

        self.pub_action = roslibpy.Topic(self.ros, "/policy/action", "dofbot_pro_info/ArmJoint")
        self.pub_action.advertise()

        self.pub_robot_cmd = roslibpy.Topic(self.ros, "/robot/cmd", "std_msgs/String")
        self.pub_robot_cmd.advertise()

    def _on_image(self, msg: dict):
        try:
            img = ros_image_to_cv2(msg)
            img = cv2.resize(img, (self.config.get("image_size", 224), self.config.get("image_size", 224)))
            img = cv2.flip(img, 0)  # Flip vertically to match data_collector.py!
            with self._lock:
                self.latest_image = img
        except Exception as e:
            pass

    def _on_joints(self, msg: dict):
        try:
            positions = msg.get("position", [])
            if len(positions) >= 6:
                # msg.position from joint_states is ALREADY in radians (matching data_collector.py)
                with self._lock:
                    self.latest_joints = [float(p) for p in positions[:6]]
        except Exception as e:
            pass

    def _on_ready(self, msg: dict):
        with self._lock:
            self.robot_ready = bool(msg.get("data", True))

    def _on_command(self, msg: dict):
        cmd = msg.get("data", "").strip()
        if cmd:
            print(f"\n[Command Received]: '{cmd}'")
            with self._lock:
                self.current_command = cmd

    def send_action(self, joints_deg: list):
        """Clamp and send 6-DoF joint command to /policy/action."""
        clamped = [
            float(np.clip(joints_deg[i], JOINT_SAFE_MIN[i], JOINT_SAFE_MAX[i]))
            for i in range(6)
        ]
        # Soft gripper ceiling
        clamped[5] = float(np.clip(clamped[5], JOINT_SAFE_MIN[5], self.args.gripper_max_deg))
        msg = roslibpy.Message({
            "joints": clamped,
            "run_time": int(1000.0 / self.args.inference_hz)
        })
        self.pub_action.publish(msg)

    def run_policy_step(self) -> Optional[np.ndarray]:
        with self._lock:
            img = self.latest_image
            joints = self.latest_joints
            cmd = self.current_command

        if img is None or joints is None:
            return None

        # Preprocess Image: (3, H, W) normalized on device
        img_tensor = torch.from_numpy(img).permute(2, 0, 1).float().to(self.device) / 255.0
        img_mean = self.stats[IMAGE_KEY]["mean"]
        img_std = self.stats[IMAGE_KEY]["std"]
        img_norm = (img_tensor - img_mean) / (img_std + 1e-8)

        # Preprocess State: joints is ALREADY in radians matching training state convention
        state_tensor = torch.tensor(joints, dtype=torch.float32, device=self.device)
        state_mean = self.stats[STATE_KEY]["mean"]
        state_std = self.stats[STATE_KEY]["std"]
        state_norm = (state_tensor - state_mean) / (state_std + 1e-8)

        # Task ID
        task_id = text_to_task_id(cmd)

        # Forward pass
        pred_actions_norm = self.policy.select_action(
            img_norm.unsqueeze(0),
            state_norm.unsqueeze(0),
            task_id
        ).cpu().numpy()  # (chunk_size, 6)

        # Denormalize Actions
        action_mean = self.stats[ACTION_KEY]["mean"].cpu().numpy()
        action_std = self.stats[ACTION_KEY]["std"].cpu().numpy()
        pred_actions_rad = pred_actions_norm * (action_std + 1e-8) + action_mean

        return pred_actions_rad

    def execute_command(self, command: str, max_duration_s: float = 25.0):
        """Execute a language command with temporal action smoothing."""
        print(f"\n=======================================================")
        print(f"Executing Policy Action for: '{command}'")
        print(f"=======================================================")
        with self._lock:
            self.current_command = command
            self.is_running_episode = True

        # Signal robot controller to start episode
        self.pub_robot_cmd.publish(roslibpy.Message({"data": "start"}))
        time.sleep(0.5)

        t_start = time.time()
        chunk_idx = 0
        step_dt = 1.0 / self.args.inference_hz

        # Temporal ensembling buffer (k_steps, 6)
        chunk_size = self.config.get("chunk_size", 16)
        action_buffer = np.zeros((chunk_size, NUM_JOINTS), dtype=np.float32)
        weight_buffer = np.zeros((chunk_size, 1), dtype=np.float32)
        exp_weights = np.exp(-0.1 * np.arange(chunk_size))[:, None]  # Exponential decay weighting

        try:
            while time.time() - t_start < max_duration_s:
                pred_chunk = self.run_policy_step()
                if pred_chunk is None:
                    print("Waiting for camera / joint observation...", end="\r")
                    time.sleep(0.1)
                    continue

                # Blend current prediction into action buffer
                action_buffer = action_buffer + pred_chunk * exp_weights
                weight_buffer = weight_buffer + exp_weights

                # Get smooth action for current step
                current_action_rad = action_buffer[0] / (weight_buffer[0] + 1e-6)
                action_deg = action_rad_to_deg(current_action_rad)
                self.send_action(action_deg)

                # Shift buffer left by 1 step
                action_buffer[:-1] = action_buffer[1:]
                action_buffer[-1] = 0.0
                weight_buffer[:-1] = weight_buffer[1:]
                weight_buffer[-1] = 0.0

                chunk_idx += 1
                elapsed = time.time() - t_start
                print(f"Step {chunk_idx:3d} executed | Elapsed: {elapsed:5.1f}s / {max_duration_s:.1f}s", end="\r")
                time.sleep(step_dt)

            print(f"\nCommand execution completed in {time.time() - t_start:.1f}s.")
        finally:
            with self._lock:
                self.is_running_episode = False


def main():
    parser = argparse.ArgumentParser(description="Real-Robot ACT Policy Inference Server")
    parser.add_argument("--checkpoint_dir", default="runs/act_dofbot_001/checkpoints/step_003000")
    parser.add_argument("--jetson_ip", default="127.0.0.1")
    parser.add_argument("--bridge_port", type=int, default=9090)
    parser.add_argument("--image_topic", default="/camera/color/image_raw")
    parser.add_argument("--inference_hz", type=float, default=10.0)
    parser.add_argument("--gripper_max_deg", type=float, default=120.0)
    parser.add_argument("--default_command", default="pick and place red cube to side area")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    server = DofBotInferenceServer(args)

    print("\nInference Server Ready! Type a language command or 'quit' to exit:")
    try:
        while True:
            cmd = input("\nEnter command (e.g. 'pick green cube', 'clear blue obstacle'): ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("q", "quit", "exit"):
                break
            server.execute_command(cmd)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        server.ros.terminate()


if __name__ == "__main__":
    main()
