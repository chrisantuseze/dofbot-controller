#!/usr/bin/env python3
# encoding: utf-8
"""
robot_controller.py  —  runs on the Jetson Orin Nano.

Role in the LeRobot stack
─────────────────────────
This script is the Jetson-side counterpart to lerobot_inference_server.py
running on the lab computer.  It sits between the incoming policy commands and
arm_driver.py, providing:

  1. Safety gate   — validates every joint command before it reaches arm_driver.
                     Commands outside safe bounds are clamped and logged.
  2. Motion sync   — publishes a /robot/ready flag so the lab server knows when
                     the arm has settled and a new command can be accepted.
  3. Episode ctrl  — manages start / stop / home-reset lifecycle so you can
                     run multiple evaluation episodes without restarting nodes.
  4. Heartbeat     — kills motion if the lab computer stops sending commands
                     (network drop, crash) within a configurable timeout.

Topic layout
─────────────
  Subscriptions (from lab computer via rosbridge):
    /policy/action   dofbot_pro_info/ArmJoint  — desired joint angles (deg)

  Publications (to arm_driver.py, already running on Jetson):
    TargetAngle      dofbot_pro_info/ArmJoint  — validated joint commands

  Publications (status, readable by lab server via rosbridge):
    /robot/ready     std_msgs/Bool  — True when arm has settled
    /robot/episode   std_msgs/String — JSON status {"state": ..., "step": ...}

  Subscriptions (episode control, can be triggered from lab or keyboard here):
    /robot/cmd       std_msgs/String — "start" | "stop" | "home" | "reset"

Startup
───────
  # On the Jetson (after roscore, rosbridge, arm_driver, camera are running):
  rosrun dofbot_policy_bridge robot_controller.py

  # The lab computer's lerobot_inference_server.py targets /policy/action
  # instead of TargetAngle directly, so all commands flow through this node.

  # Override the action topic if testing without this node:
  #   set POLICY_ACTION_TOPIC=TargetAngle in the inference server to bypass.

Relationship to unveiler_grasp.py
──────────────────────────────────
  unveiler_grasp.py (SRE-RL)          robot_controller.py (LeRobot)
  ─────────────────────────           ──────────────────────────────
  Packages custom ObservData          Not needed — server subscribes to
    and publishes to /action/obs        standard /joint_states + /camera
  Busy-waits for /action/data         Not needed — server streams commands
  Runs IK (kinemarics service)        Not needed — policy outputs joint pos
  Executes full grasp sequence        Validates + forwards to arm_driver
  Episode loop with input()           Episode loop with /robot/cmd topic
"""

import json
import math
import threading
import time
from typing import Optional

import numpy as np
import rospy
from std_msgs.msg import Bool, String
from sensor_msgs.msg import JointState

from dofbot_pro_info.msg import ArmJoint

# ── Joint safety limits (servo degrees) ──────────────────────────────────────
# Source: URDF joint_limits.yaml + hardware datasheet.
# All values are in degrees and represent the safe operating range.
JOINT_SAFE_MIN = [  0.0,  30.0,   0.0,   0.0,   0.0,  30.0]
JOINT_SAFE_MAX = [180.0, 270.0, 180.0, 270.0, 180.0, 180.0]

# Home position (degrees) — matches arm_driver.py initialisation
JOINTS_HOME = [90.0, 90.0, 90.0, 0.0, 90.0, 30.0]

NUM_JOINTS = 6

# How close (degrees) all joints must be to their targets before we declare
# "settled" and flip /robot/ready to True.
SETTLED_THRESHOLD_DEG = 2.0

# Time (seconds) without a new /policy/action message before triggering
# the heartbeat safety stop.
HEARTBEAT_TIMEOUT = 3.0

# ── Episode states ────────────────────────────────────────────────────────────
STATE_IDLE    = "idle"      # waiting for "start" command
STATE_RUNNING = "running"   # accepting and forwarding policy actions
STATE_HOMING  = "homing"    # moving to home position


class RobotController:
    def __init__(self):
        rospy.init_node("robot_controller_node", anonymous=False)

        # Parameters
        self.settled_threshold = float(
            rospy.get_param("~settled_threshold_deg", SETTLED_THRESHOLD_DEG))
        self.heartbeat_timeout = float(
            rospy.get_param("~heartbeat_timeout_s", HEARTBEAT_TIMEOUT))
        self.home_move_time    = int(
            rospy.get_param("~home_move_time_ms", 3000))
        self.step_move_time    = int(
            rospy.get_param("~step_move_time_ms", 200))
        self.autostart         = rospy.get_param("~autostart", False)

        # State
        self._lock              = threading.Lock()
        self._episode_state     = STATE_IDLE
        self._episode_step      = 0
        self._current_joints    = np.array(JOINTS_HOME, dtype=np.float32)
        self._target_joints     = np.array(JOINTS_HOME, dtype=np.float32)
        self._last_action_time  = 0.0   # epoch seconds of last /policy/action msg

        # Publishers
        self._cmd_pub    = rospy.Publisher(
            "TargetAngle", ArmJoint, queue_size=1)
        self._ready_pub  = rospy.Publisher(
            "/robot/ready", Bool, queue_size=1, latch=True)
        self._status_pub = rospy.Publisher(
            "/robot/episode", String, queue_size=1, latch=True)

        # Subscribers
        rospy.Subscriber(
            "/policy/action", ArmJoint, self._cb_policy_action, queue_size=1)
        rospy.Subscriber(
            "/joint_states", JointState, self._cb_joint_states, queue_size=1)
        rospy.Subscriber(
            "/robot/cmd", String, self._cb_cmd, queue_size=10)

        rospy.loginfo("[RobotController] Initialised. autostart=%s", self.autostart)
        self._publish_status()

        if self.autostart:
            self._start_episode()

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _cb_policy_action(self, msg: ArmJoint):
        """
        Receives a joint command from lerobot_inference_server.py.
        Only accepted while the episode is in STATE_RUNNING.
        """
        with self._lock:
            if self._episode_state != STATE_RUNNING:
                rospy.logwarn_throttle(
                    2.0,
                    "[RobotController] Action received but episode not running "
                    "(state=%s). Send /robot/cmd 'start' to begin.",
                    self._episode_state,
                )
                return

            if len(msg.joints) != NUM_JOINTS:
                rospy.logwarn(
                    "[RobotController] Expected %d joints, got %d — ignoring.",
                    NUM_JOINTS, len(msg.joints),
                )
                return

            # Safety clamp
            raw     = list(msg.joints)
            clamped = self._clamp_joints(raw)
            if clamped != raw:
                rospy.logwarn(
                    "[RobotController] Joint command clamped: %s → %s",
                    [f"{v:.1f}" for v in raw],
                    [f"{v:.1f}" for v in clamped],
                )

            self._target_joints  = np.array(clamped, dtype=np.float32)
            self._last_action_time = time.time()
            self._episode_step  += 1

        # Forward the (clamped) command to arm_driver.py
        out                = ArmJoint()
        out.joints         = clamped
        out.run_time       = msg.run_time if msg.run_time > 0 else self.step_move_time
        self._cmd_pub.publish(out)

        # Mark not-ready until the arm settles at the new target
        self._ready_pub.publish(Bool(data=False))
        self._publish_status()

    def _cb_joint_states(self, msg: JointState):
        """Track current joint positions (radians → degrees for comparison)."""
        JOINT_NAMES = ["Arm1_Joint", "Arm2_Joint", "Arm3_Joint",
                       "Arm4_Joint", "Arm5_Joint", "grip_joint"]
        name_to_idx = {n: i for i, n in enumerate(msg.name)}
        RAD2DEG = 180.0 / math.pi

        joints_deg = list(self._current_joints)
        for k, jname in enumerate(JOINT_NAMES):
            if jname in name_to_idx:
                rad = float(msg.position[name_to_idx[jname]])
                # Reverse the arm_driver offset: position = (deg-90)*pi/180
                if k < 5:
                    joints_deg[k] = rad * RAD2DEG + 90.0
                else:
                    # grip: interp [30,180]→[0,90] in arm_driver
                    d_state = rad * RAD2DEG + 90.0
                    joints_deg[k] = float(np.interp(
                        d_state, [0.0, 90.0], [30.0, 180.0]))

        print("Current joints (deg): ", [f"{j:.1f}" for j in joints_deg])
        with self._lock:
            self._current_joints = np.array(joints_deg, dtype=np.float32)

    def _cb_cmd(self, msg: String):
        """
        Episode control commands from /robot/cmd.

        Accepted values:
          "start"   — begin a new episode (arm must be near home)
          "stop"    — end current episode, stay in place
          "home"    — move to home position, then idle
          "reset"   — home + start a fresh episode
        """
        cmd = msg.data.strip().lower()
        rospy.loginfo("[RobotController] Received cmd: '%s'", cmd)

        if cmd == "start":
            self._start_episode()
        elif cmd == "stop":
            self._stop_episode()
        elif cmd == "home":
            self._go_home()
        elif cmd == "reset":
            self._go_home()
            rospy.sleep(self.home_move_time / 1000.0 + 0.5)
            self._start_episode()
        else:
            rospy.logwarn("[RobotController] Unknown cmd: '%s'", cmd)

    # ── Episode management ────────────────────────────────────────────────────

    def _start_episode(self):
        with self._lock:
            self._episode_state = STATE_RUNNING
            self._episode_step  = 0
            self._last_action_time = time.time()
        self._ready_pub.publish(Bool(data=True))
        self._publish_status()
        rospy.loginfo("[RobotController] Episode started — accepting policy actions.")

    def _stop_episode(self):
        with self._lock:
            self._episode_state = STATE_IDLE
        self._ready_pub.publish(Bool(data=False))
        self._publish_status()
        rospy.loginfo("[RobotController] Episode stopped after %d steps.",
                      self._episode_step)

    def _go_home(self):
        rospy.loginfo("[RobotController] Moving to home position…")
        with self._lock:
            self._episode_state  = STATE_HOMING
            self._target_joints  = np.array(JOINTS_HOME, dtype=np.float32)
        self._publish_status()
        self._ready_pub.publish(Bool(data=False))

        msg          = ArmJoint()
        msg.joints   = JOINTS_HOME
        msg.run_time = self.home_move_time
        self._cmd_pub.publish(msg)

        # Wait for motion to complete before declaring idle
        rospy.sleep(self.home_move_time / 1000.0 + 0.5)
        with self._lock:
            self._episode_state = STATE_IDLE
        self._publish_status()
        rospy.loginfo("[RobotController] Home reached.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clamp_joints(self, joints: list) -> list:
        return [
            float(np.clip(j, JOINT_SAFE_MIN[i], JOINT_SAFE_MAX[i]))
            for i, j in enumerate(joints[:NUM_JOINTS])
        ]

    def _is_settled(self) -> bool:
        with self._lock:
            diff = np.abs(self._current_joints - self._target_joints)
        return bool(np.all(diff < self.settled_threshold))

    def _publish_status(self):
        with self._lock:
            payload = {
                "state": self._episode_state,
                "step":  self._episode_step,
            }
        self._status_pub.publish(String(data=json.dumps(payload)))

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        rate = rospy.Rate(20)  # 20 Hz monitor loop
        while not rospy.is_shutdown():
            with self._lock:
                state      = self._episode_state
                last_action = self._last_action_time

            if state == STATE_RUNNING:
                # Heartbeat check — stop if lab server has gone silent
                if (time.time() - last_action) > self.heartbeat_timeout:
                    rospy.logwarn(
                        "[RobotController] No action received for %.1f s — "
                        "stopping episode (heartbeat timeout).",
                        self.heartbeat_timeout,
                    )
                    self._stop_episode()

                # Notify lab server that arm has settled at the target
                elif self._is_settled():
                    self._ready_pub.publish(Bool(data=True))

            rate.sleep()


if __name__ == "__main__":
    ctrl = RobotController()
    ctrl.run()
