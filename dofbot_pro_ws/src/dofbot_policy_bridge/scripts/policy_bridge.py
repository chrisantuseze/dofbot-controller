#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
policy_bridge.py
================
Connects the Dofbot Pro to any LeRobot-compatible policy model (ACT, Diffusion
Policy, pi0, etc.).

Flow:
  1. Subscribe to /joint_states and /camera/color/image_raw
  2. Build an observation dict that matches the LeRobot env format
  3. Call the policy (loaded locally or via a simple HTTP inference server)
  4. Convert the output joint-position action (radians) to degrees and publish
     to the TargetAngle topic consumed by arm_driver.py

Usage:
  # --- Step 1: Smoke-test the pipeline with no ML model ---
  # Moves the arm through a safe canned sequence so you can verify the full
  # chain (ROS topics → bridge → servo commands) before loading real weights.
  rosrun dofbot_policy_bridge policy_bridge.py \
      _policy_type:=mock \
      _inference_hz:=0.2          # one waypoint every 5 s — adjust as needed

  # --- Step 2: Try a pre-trained HuggingFace checkpoint (no training needed) ---
  # lerobot/act_koch_real is trained on a 6-DOF arm with similar kinematics.
  # It won't perform the exact task, but proves inference + joint mapping work.
  rosrun dofbot_policy_bridge policy_bridge.py \
      _policy_type:=pretrained \
      _pretrained_repo:=lerobot/act_koch_real \
      _inference_hz:=10

  # --- Step 3: Local checkpoint after fine-tuning ---
  rosrun dofbot_policy_bridge policy_bridge.py \
      _policy_type:=act \
      _checkpoint_path:=/path/to/checkpoint \
      _inference_hz:=10 \
      _move_time_ms:=100

  # --- Step 4: Remote inference server ---
  rosrun dofbot_policy_bridge policy_bridge.py \
      _policy_type:=server \
      _server_url:=http://localhost:8000/predict \
      _inference_hz:=10

Joint mapping (Dofbot Pro):
  Index  ROS name      Degrees  Radians
  0      Arm1_Joint    0–180    -π/2 to +π/2
  1      Arm2_Joint    0–270    hardware range
  2      Arm3_Joint    0–180
  3      Arm4_Joint    0–270
  4      Arm5_Joint    0–180
  5      grip_joint    30–180   (30 = open, 180 = closed)
"""

import math
import threading
import time
from typing import List, Optional

import numpy as np
import rospy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import Float32MultiArray

# Local custom messages
from dofbot_pro_info.msg import ArmJoint

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Joint neutral positions (degrees) used by arm_driver.py
JOINTS_HOME_DEG = [90.0, 90.0, 90.0, 0.0, 90.0, 30.0]
# Number of controllable joints
NUM_JOINTS = 6
# arm_driver offsets: joint_state_rad = (joint_deg - 90) * pi/180
# Inverse: joint_deg = joint_rad * 180/pi + 90
RAD2DEG = 180.0 / math.pi
# Gripper is on a different scale: degrees 30-180 maps to 0-90 in joint_states
GRIPPER_MIN_DEG = 30.0
GRIPPER_MAX_DEG = 180.0
GRIPPER_STATE_MIN_DEG = 0.0
GRIPPER_STATE_MAX_DEG = 90.0


def joint_state_rad_to_deg(joints_rad: List[float]) -> List[float]:
    """Convert joint_states (radians, offset from 90°) back to servo degrees."""
    deg = []
    for i, r in enumerate(joints_rad):
        if i < 5:
            # arm_driver: position = (deg - 90) * pi/180
            d = r * RAD2DEG + 90.0
        else:
            # grip_joint: interp [30,180] → [0,90], so inverse: [0,90] → [30,180]
            d_state = r * RAD2DEG + 90.0  # undo the -90 offset first
            d = np.interp(d_state, [GRIPPER_STATE_MIN_DEG, GRIPPER_STATE_MAX_DEG],
                          [GRIPPER_MIN_DEG, GRIPPER_MAX_DEG])
        deg.append(float(np.clip(d, 0.0, 270.0)))
    return deg


def policy_action_to_deg(action: np.ndarray) -> List[float]:
    """
    Convert a policy output action vector to Dofbot degree commands.

    Policies trained with LeRobot output joint positions in radians relative
    to the URDF zero (which is the 90° servo position for this robot).
    This is the same convention as /joint_states, so we reuse the converter.
    """
    return joint_state_rad_to_deg(list(action.flatten()[:NUM_JOINTS]))


# ---------------------------------------------------------------------------
# Policy loaders
# ---------------------------------------------------------------------------

class MockPolicy:
    """
    No ML required.  Cycles through a pre-defined list of joint waypoints
    (in degrees) so you can verify the full pipeline is wired up correctly
    before loading any real model weights.

    Safety notes:
      - All waypoints are near the home position with small offsets.
      - move_time_ms is deliberately long (set _move_time_ms:=1000 or more
        when running mock mode so the servos move slowly).
      - Watch the robot the first time and keep your hand near the power switch.
    """
    # Waypoints in degrees: [Arm1, Arm2, Arm3, Arm4, Arm5, grip]
    # Each step moves one joint slightly from home so you can observe each
    # servo responding independently.
    _WAYPOINTS = [
        [90.0,  90.0,  90.0,  0.0,  90.0,  30.0],   # home
        [100.0, 90.0,  90.0,  0.0,  90.0,  30.0],   # Arm1 +10°
        [90.0, 100.0,  90.0,  0.0,  90.0,  30.0],   # Arm2 +10°
        [90.0,  90.0, 100.0,  0.0,  90.0,  30.0],   # Arm3 +10°
        [90.0,  90.0,  90.0, 10.0,  90.0,  30.0],   # Arm4 +10°
        [90.0,  90.0,  90.0,  0.0, 100.0,  30.0],   # Arm5 +10°
        [90.0,  90.0,  90.0,  0.0,  90.0, 100.0],   # gripper close
        [90.0,  90.0,  90.0,  0.0,  90.0,  30.0],   # home (gripper open)
    ]

    def __init__(self):
        self._step = 0
        rospy.loginfo("[PolicyBridge] MockPolicy loaded — %d waypoints",
                      len(self._WAYPOINTS))

    def predict(self, obs: dict) -> np.ndarray:
        """Return the next waypoint as a radians array (convention: (deg-90)*pi/180)."""
        deg = self._WAYPOINTS[self._step % len(self._WAYPOINTS)]
        self._step += 1
        # Convert degrees → radians using the same convention as /joint_states
        rad = [(d - 90.0) * (math.pi / 180.0) for d in deg[:5]]
        # Gripper: interp [30,180] → [0,90] then apply same offset
        grip_state = float(np.interp(deg[5], [GRIPPER_MIN_DEG, GRIPPER_MAX_DEG],
                                     [GRIPPER_STATE_MIN_DEG, GRIPPER_STATE_MAX_DEG]))
        rad.append((grip_state - 90.0) * (math.pi / 180.0))
        rospy.loginfo("[MockPolicy] Waypoint %d: %s deg",
                      (self._step - 1) % len(self._WAYPOINTS), deg)
        return np.array(rad, dtype=np.float32)


class PretrainedLeRobotPolicy:
    """
    Load any policy checkpoint directly from the HuggingFace Hub using
    LeRobot's from_pretrained() API.  No local training needed.

    Recommended starting checkpoints for a 6-DOF arm:
      lerobot/act_koch_real          - ACT, Koch v1.1 real robot
      lerobot/diffusion_pusht        - Diffusion Policy (2D pushing)
      lerobot/act_aloha_sim_transfer_cube_human  - ACT on ALOHA sim

    Install LeRobot first:
        pip install lerobot
    """
    def __init__(self, repo_id: str, device: str = "cpu"):
        from lerobot.common.policies.factory import make_policy_from_pretrained
        import torch
        self._torch = torch
        self.device = device
        self.policy = make_policy_from_pretrained(repo_id)
        self.policy = self.policy.to(device)
        self.policy.eval()
        rospy.loginfo("[PolicyBridge] Pretrained policy loaded: %s", repo_id)

    def predict(self, obs: dict) -> np.ndarray:
        import torch
        image = torch.from_numpy(obs["image"]).float().unsqueeze(0).to(self.device)
        state = torch.from_numpy(obs["state"]).float().unsqueeze(0).to(self.device)
        with torch.no_grad():
            action = self.policy.select_action({"observation.image": image,
                                                "observation.state": state})
        # action shape may be (1, T, 6) for chunked policies — take first step
        a = action.cpu().numpy()
        if a.ndim == 3:
            a = a[0, 0]   # first batch, first timestep
        elif a.ndim == 2:
            a = a[0]
        return a.flatten()[:NUM_JOINTS].astype(np.float32)


class LocalACTPolicy:
    """
    Thin wrapper around a LeRobot ACT checkpoint.

    Install LeRobot first:
        pip install lerobot
    """
    def __init__(self, checkpoint_path: str, device: str = "cpu"):
        from lerobot.common.policies.act.modeling_act import ACTPolicy
        from lerobot.common.utils.utils import init_hydra_config
        import torch

        self._torch = torch
        cfg = init_hydra_config(checkpoint_path)
        self.policy = ACTPolicy(cfg.policy)
        state_dict = torch.load(
            f"{checkpoint_path}/model.pt", map_location=device
        )
        self.policy.load_state_dict(state_dict)
        self.policy.eval()
        self.device = device
        rospy.loginfo("[PolicyBridge] ACT policy loaded from %s", checkpoint_path)

    def predict(self, obs: dict) -> np.ndarray:
        import torch
        image = torch.from_numpy(obs["image"]).float().unsqueeze(0).to(self.device)
        state = torch.from_numpy(obs["state"]).float().unsqueeze(0).to(self.device)
        with torch.no_grad():
            action = self.policy.select_action({"observation.image": image,
                                                "observation.state": state})
        return action.cpu().numpy().squeeze(0)


class LocalDiffusionPolicy:
    """
    Wrapper for a LeRobot Diffusion Policy checkpoint.
    """
    def __init__(self, checkpoint_path: str, device: str = "cpu"):
        from lerobot.common.policies.diffusion.modeling_diffusion import DiffusionPolicy
        from lerobot.common.utils.utils import init_hydra_config
        import torch

        self._torch = torch
        cfg = init_hydra_config(checkpoint_path)
        self.policy = DiffusionPolicy(cfg.policy)
        state_dict = torch.load(
            f"{checkpoint_path}/model.pt", map_location=device
        )
        self.policy.load_state_dict(state_dict)
        self.policy.eval()
        self.device = device
        rospy.loginfo("[PolicyBridge] Diffusion policy loaded from %s", checkpoint_path)

    def predict(self, obs: dict) -> np.ndarray:
        import torch
        image = torch.from_numpy(obs["image"]).float().unsqueeze(0).to(self.device)
        state = torch.from_numpy(obs["state"]).float().unsqueeze(0).to(self.device)
        with torch.no_grad():
            action = self.policy.select_action({"observation.image": image,
                                                "observation.state": state})
        return action.cpu().numpy().squeeze(0)


class RemoteInferenceServer:
    """
    Sends observations to a simple HTTP inference server and receives actions.

    Expected server contract:
        POST /predict
        Body: {"image": <base64 RGB>, "state": [j1,...,j6]}
        Response: {"action": [j1,...,j6]}  (radians)
    """
    def __init__(self, url: str):
        import urllib.request, json as _json, base64 as _b64
        self._url = url
        self._json = _json
        self._b64 = _b64
        self._urllib = urllib
        rospy.loginfo("[PolicyBridge] Using remote inference server at %s", url)

    def predict(self, obs: dict) -> np.ndarray:
        import cv2, json, base64, urllib.request
        _, buf = cv2.imencode(".jpg", obs["image_bgr"])
        img_b64 = base64.b64encode(buf).decode("utf-8")
        payload = json.dumps({
            "image": img_b64,
            "state": obs["state"].tolist()
        }).encode()
        req = urllib.request.Request(
            self._url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            result = json.loads(resp.read())
        return np.array(result["action"], dtype=np.float32)


# ---------------------------------------------------------------------------
# Bridge node
# ---------------------------------------------------------------------------

class PolicyBridgeNode:
    def __init__(self):
        rospy.init_node("policy_bridge_node", anonymous=False)

        # Parameters
        policy_type    = rospy.get_param("~policy_type", "mock")
        checkpoint     = rospy.get_param("~checkpoint_path", "")
        pretrained_repo= rospy.get_param("~pretrained_repo", "lerobot/act_koch_real")
        server_url     = rospy.get_param("~server_url", "http://localhost:8000/predict")
        device         = rospy.get_param("~device", "cpu")
        self.hz        = float(rospy.get_param("~inference_hz", 10.0))
        self.move_time = int(rospy.get_param("~move_time_ms", 500))
        self.enabled   = rospy.get_param("~autostart", True)
        img_h          = int(rospy.get_param("~image_height", 224))
        img_w          = int(rospy.get_param("~image_width", 224))
        self.img_size  = (img_h, img_w)

        # Policy loading
        if policy_type == "mock":
            self.policy = MockPolicy()
        elif policy_type == "pretrained":
            self.policy = PretrainedLeRobotPolicy(pretrained_repo, device)
        elif policy_type == "act":
            self.policy = LocalACTPolicy(checkpoint, device)
        elif policy_type == "diffusion":
            self.policy = LocalDiffusionPolicy(checkpoint, device)
        elif policy_type == "server":
            self.policy = RemoteInferenceServer(server_url)
        else:
            rospy.logfatal("[PolicyBridge] Unknown policy_type '%s'. "
                           "Use: mock | pretrained | act | diffusion | server",
                           policy_type)
            raise ValueError(f"Unknown policy_type: {policy_type}")

        # State
        self._bridge       = CvBridge()
        self._lock         = threading.Lock()
        self._latest_image: Optional[np.ndarray] = None   # (H, W, 3) uint8 BGR
        self._latest_state: Optional[np.ndarray] = None   # (6,) radians
        self._image_stamp  = rospy.Time(0)
        self._state_stamp  = rospy.Time(0)

        # Publishers
        self._cmd_pub = rospy.Publisher("TargetAngle", ArmJoint, queue_size=1)

        # Subscribers
        rospy.Subscriber("/camera/color/image_raw", Image, self._cb_image,
                         queue_size=1, buff_size=2**24)
        rospy.Subscriber("/joint_states", JointState, self._cb_joint_states,
                         queue_size=1)

        rospy.loginfo("[PolicyBridge] Initialized. enabled=%s, hz=%.1f",
                      self.enabled, self.hz)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _cb_image(self, msg: Image):
        import cv2
        try:
            bgr = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            bgr = cv2.resize(bgr, (self.img_size[1], self.img_size[0]))
            with self._lock:
                self._latest_image = bgr
                self._image_stamp  = msg.header.stamp
        except Exception as e:
            rospy.logwarn_throttle(5.0, "[PolicyBridge] Image callback error: %s", e)

    def _cb_joint_states(self, msg: JointState):
        # JointState ordering may vary; match by name
        name_to_idx = {n: i for i, n in enumerate(msg.name)}
        joint_names  = ["Arm1_Joint", "Arm2_Joint", "Arm3_Joint",
                        "Arm4_Joint", "Arm5_Joint", "grip_joint"]
        state = np.zeros(NUM_JOINTS, dtype=np.float32)
        for k, jname in enumerate(joint_names):
            if jname in name_to_idx:
                state[k] = msg.position[name_to_idx[jname]]
        with self._lock:
            self._latest_state = state
            self._state_stamp  = msg.header.stamp

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _observations_ready(self) -> bool:
        max_age = rospy.Duration(1.0)
        now = rospy.Time.now()
        return (self._latest_image is not None and
                self._latest_state is not None and
                (now - self._image_stamp) < max_age and
                (now - self._state_stamp) < max_age)

    def _build_obs(self):
        """Build the observation dict expected by all supported policies."""
        import cv2
        bgr = self._latest_image.copy()
        # Policies expect RGB, channels-first, normalized to [-1, 1] or [0, 1]
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        image_chw = np.transpose(rgb, (2, 0, 1)).astype(np.float32) / 255.0
        return {
            "image":     image_chw,          # (3, H, W) float32 [0, 1]
            "image_bgr": bgr,                # (H, W, 3) uint8  for server mode
            "state":     self._latest_state  # (6,) float32 radians
        }

    def _publish_action(self, deg_commands: List[float]):
        msg = ArmJoint()
        msg.joints = [float(d) for d in deg_commands]
        msg.run_time = self.move_time
        self._cmd_pub.publish(msg)
        rospy.logdebug("[PolicyBridge] Published: %s", msg.joints)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        rate = rospy.Rate(self.hz)
        while not rospy.is_shutdown():
            if not self.enabled:
                rate.sleep()
                continue

            with self._lock:
                ready = self._observations_ready()
                obs   = self._build_obs() if ready else None

            if not ready:
                rospy.logwarn_throttle(3.0,
                    "[PolicyBridge] Waiting for observations "
                    "(image=%s, state=%s)...",
                    self._latest_image is not None,
                    self._latest_state is not None)
                rate.sleep()
                continue

            try:
                t0 = time.time()
                action = self.policy.predict(obs)       # (6,) radians
                dt = (time.time() - t0) * 1000.0
                rospy.logdebug("[PolicyBridge] Inference: %.1f ms", dt)

                deg_cmds = policy_action_to_deg(action)
                self._publish_action(deg_cmds)
            except Exception as e:
                rospy.logerr("[PolicyBridge] Inference error: %s", e)

            rate.sleep()


if __name__ == "__main__":
    node = PolicyBridgeNode()
    node.run()
