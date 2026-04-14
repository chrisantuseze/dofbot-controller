#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_collector.py
=================
Records synchronized (image, joint_state, action) episodes for training
robot manipulation policies with LeRobot.

The node records episodes in LeRobot HDF5 format compatible with
`lerobot.common.datasets.lerobot_dataset.LeRobotDataset`.

Usage:
    # Start recording a new episode:
    rosrun dofbot_policy_bridge data_collector.py \
        _output_dir:=/data/dofbot_dataset \
        _episode_index:=0 \
        _record_hz:=30

    Control via keyboard (or ROS topics):
        r  - start / resume recording
        s  - stop and save current episode
        q  - quit

    Via /robot/cmd topic:
        "record"  - start recording  (NOT "start", which enables the arm)
        "stop"    - stop and save
        "discard" - discard current episode

Key topics listened to:
    /camera/color/image_raw  (sensor_msgs/Image)
    /joint_states            (sensor_msgs/JointState)
    /ArmAngleUpdate          (ArmJoint) -- used as the "action" label
"""

import math
import os
import threading
import time

import cv2
import h5py
import numpy as np
import rospy
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import String

from dofbot_pro_info.msg import ArmJoint

# ---------------------------------------------------------------------------
# Constants (match policy_bridge.py)
# ---------------------------------------------------------------------------
NUM_JOINTS = 6
RAD2DEG = 180.0 / math.pi
JOINT_NAMES = ["Arm1_Joint", "Arm2_Joint", "Arm3_Joint",
               "Arm4_Joint", "Arm5_Joint", "grip_joint"]


class DataCollectorNode:
    def __init__(self):
        rospy.init_node("data_collector_node", anonymous=False)

        # Parameters
        self.output_dir    = rospy.get_param("~output_dir", "/tmp/dofbot_dataset")
        self.episode_idx   = int(rospy.get_param("~episode_index", 0))
        self.record_hz     = float(rospy.get_param("~record_hz", 15.0))
        self.img_h         = int(rospy.get_param("~image_height", 224))
        self.img_w         = int(rospy.get_param("~image_width", 224))

        os.makedirs(self.output_dir, exist_ok=True, )

        self._bridge     = CvBridge()
        self._lock       = threading.Lock()

        # Latest sensor readings
        self._latest_image: np.ndarray | None = None
        self._latest_state: np.ndarray | None = None
        self._latest_action: np.ndarray | None = None  # from /ArmAngleUpdate

        # Episode buffers
        self._images:  list[np.ndarray] = []  # (H, W, 3) uint8 RGB
        self._states:  list[np.ndarray] = []  # (6,) float32 radians
        self._actions: list[np.ndarray] = []  # (6,) float32 radians

        # Control flags
        self._recording = False
        self._frame_count = 0

        # Subscribers
        rospy.Subscriber("/camera/color/image_raw", Image,
                         self._cb_image, queue_size=1, buff_size=2**24)
        rospy.Subscriber("/joint_states", JointState,
                         self._cb_joint_states, queue_size=1)
        rospy.Subscriber("ArmAngleUpdate", ArmJoint,
                         self._cb_action, queue_size=1)
        rospy.Subscriber("/robot/cmd", String,
                         self._cb_cmd, queue_size=10)

        rospy.loginfo("[DataCollector] Ready. Episode index=%d, output=%s",
                      self.episode_idx, self.output_dir)
        rospy.loginfo("[DataCollector] Call start_recording() / stop_recording() "
                      "or use keyboard: r=record, s=save, q=quit")

    # ------------------------------------------------------------------
    # Subscribers
    # ------------------------------------------------------------------

    def _cb_image(self, msg: Image):
        try:
            bgr = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            bgr = cv2.resize(bgr, (self.img_w, self.img_h))
            bgr = cv2.flip(bgr, 0)  # flip vertically (top ↔ bottom)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            with self._lock:
                self._latest_image = rgb
        except Exception as e:
            rospy.logwarn_throttle(5.0, "[DataCollector] Image error: %s", e)

    def _cb_joint_states(self, msg: JointState):
        name_to_idx = {n: i for i, n in enumerate(msg.name)}
        state = np.zeros(NUM_JOINTS, dtype=np.float32)
        for k, jname in enumerate(JOINT_NAMES):
            if jname in name_to_idx:
                state[k] = float(msg.position[name_to_idx[jname]])
        with self._lock:
            self._latest_state = state

    def _cb_action(self, msg: ArmJoint):
        """
        ArmAngleUpdate carries the commanded joint angles in degrees.
        Convert to radians for storage (policy-friendly format).
        """
        if len(msg.joints) == NUM_JOINTS:
            # Convert degrees to radians (same convention as joint_states)
            joints_deg = np.array(msg.joints[:NUM_JOINTS], dtype=np.float32)
            joints_rad = (joints_deg - 90.0) * (math.pi / 180.0)
            with self._lock:
                self._latest_action = joints_rad

    # ------------------------------------------------------------------
    # Recording control
    # ------------------------------------------------------------------

    def _cb_cmd(self, msg: String):
        """Handle recording commands from gamepad_teleop or any publisher.

        NOTE: "start" is intentionally NOT handled here — that command is
        used to enable the arm driver and is published as a latched message
        that would otherwise auto-start recording on node startup.
        Send "record" to begin recording instead.
        """
        cmd = msg.data.strip().lower()
        if cmd == "record":
            self.start_recording()
        elif cmd in ("stop", "save"):
            self.stop_recording()
        elif cmd == "discard":
            self.discard_episode()
        # "home" is a robot motion command — nothing to do for the recorder

    def start_recording(self):
        with self._lock:
            self._images.clear()
            self._states.clear()
            self._actions.clear()
            self._frame_count = 0
            self._recording = True
        rospy.loginfo("[DataCollector] Recording started for episode %d.",
                      self.episode_idx)

    def discard_episode(self):
        """Abort recording and discard all buffered frames without saving."""
        with self._lock:
            self._recording = False
            self._images.clear()
            self._states.clear()
            self._actions.clear()
            self._frame_count = 0
        rospy.logwarn(
            "[DataCollector] Episode discarded. Next episode index: %d",
            self.episode_idx)

    def stop_recording(self) -> str:
        with self._lock:
            self._recording = False
            n = self._frame_count

        if n == 0:
            rospy.logwarn("[DataCollector] No frames recorded, nothing saved.")
            return ""

        path = self._save_episode()
        rospy.loginfo("[DataCollector] Saved %d frames → %s", n, path)
        self.episode_idx += 1
        return path

    # ------------------------------------------------------------------
    # Recording loop
    # ------------------------------------------------------------------

    def _record_frame(self):
        """Called at record_hz. Snapshot buffers under lock."""
        with self._lock:
            if not self._recording:
                return
            if (self._latest_image is None or
                    self._latest_state is None or
                    self._latest_action is None):
                return
            self._images.append(self._latest_image.copy())
            self._states.append(self._latest_state.copy())
            self._actions.append(self._latest_action.copy())
            self._frame_count += 1

    # ------------------------------------------------------------------
    # HDF5 serialisation (LeRobot-compatible)
    # ------------------------------------------------------------------

    def _save_episode(self) -> str:
        fname = os.path.join(
            self.output_dir,
            f"episode_{self.episode_idx:06d}.hdf5"
        )
        with self._lock:
            images  = np.stack(self._images,  axis=0)   # (T, H, W, 3)
            states  = np.stack(self._states,  axis=0)   # (T, 6)
            actions = np.stack(self._actions, axis=0)   # (T, 6)

        with h5py.File(fname, "w") as f:
            # LeRobot expected keys
            f.create_dataset("observation/images/top",
                             data=images, compression="lzf")
            f.create_dataset("observation/state",
                             data=states, compression="lzf")
            f.create_dataset("action",
                             data=actions, compression="lzf")
            # Metadata
            f.attrs["fps"]           = self.record_hz
            f.attrs["episode_index"] = self.episode_idx
            f.attrs["num_frames"]    = len(images)
            f.attrs["robot"]         = "dofbot_pro"
            f.attrs["joint_names"]   = JOINT_NAMES
        return fname

    # ------------------------------------------------------------------
    # Main loop with keyboard control
    # ------------------------------------------------------------------

    def run(self):
        import sys
        import select
        import termios
        import tty

        # Save terminal settings so we can restore on exit
        old_settings = None
        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except Exception:
            rospy.logwarn("[DataCollector] Keyboard control unavailable "
                          "(non-interactive terminal). Use ROS service or "
                          "call start_recording()/stop_recording() directly.")
            old_settings = None

        rate = rospy.Rate(self.record_hz)
        rospy.loginfo("[DataCollector] Keys: r=record, s=stop+save, q=quit  |  topic /robot/cmd: \"record\"=start, \"stop\"=save, \"discard\"=discard")

        try:
            while not rospy.is_shutdown():
                # Non-blocking key read
                if old_settings is not None:
                    rlist, _, _ = select.select([sys.stdin], [], [], 0)
                    if rlist:
                        key = sys.stdin.read(1)
                        if key == "r":
                            self.start_recording()
                        elif key == "s":
                            self.stop_recording()
                        elif key == "q":
                            break

                self._record_frame()
                rate.sleep()
        finally:
            if old_settings is not None:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            rospy.loginfo("[DataCollector] Exiting. Episodes saved: %d",
                          self.episode_idx)


if __name__ == "__main__":
    node = DataCollectorNode()
    node.run()
