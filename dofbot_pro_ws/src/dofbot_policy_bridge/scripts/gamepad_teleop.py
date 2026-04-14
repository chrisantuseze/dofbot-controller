#!/usr/bin/env python3
# encoding: utf-8
"""
gamepad_teleop.py — USB gamepad teleoperation for the Dofbot Pro.
                    For recording pick-and-place demonstrations.

Confirmed controller mapping (joystick index 0):
─────────────────────────────────────────────────────────────────────
  axis_j0  left  stick X  (axis 0) → j0  base rotation
  axis_j1  left  stick Y  (axis 1) → j1  shoulder (north = up, inverted)
  axis_j2  (axis -1)               → j2  elbow twist — NOT YET MAPPED
  axis_j3  right stick Y  (axis 3) → j3  wrist pitch (north = down)
  axis_j5  right stick X  (axis 5) → j5  gripper open (positive half only)

  btn_gripper_close (btn 8, held)  → j5  gripper close
  btn_j4_pos        (btn 3, held)  → j4  twist positive
  btn_j4_neg        (-1 = off)     → j4  twist negative

  btn_start_rec (btn 0)  A — start recording
  btn_stop_rec  (btn 1)  B — stop + save
  btn_discard   (btn 2)  X — discard + home

All mappings live in config/gamepad_config.yaml — edit that file to
change any button or axis assignment permanently.

Topics published:
  TargetAngle   dofbot_pro_info/ArmJoint  — joint commands for arm_driver.py
  /robot/cmd    std_msgs/String           — "record" | "stop" | "discard"
"""

import os
import threading

# On headless systems (no display) SDL2 needs a dummy video driver so
# that event.pump() actually processes joystick events.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# SDL2 uses udev to enumerate joysticks; without being in the 'input' group
# (requires re-login after usermod) it finds nothing.  Set the device path
# explicitly as a fallback so the node works in the current session.
os.environ.setdefault("SDL_JOYSTICK_DEVICE", "/dev/input/js0")

import pygame
import rospy
from std_msgs.msg import String

from dofbot_pro_info.msg import ArmJoint

# ── Joint safety limits (degrees) ────────────────────────────────────────────
JOINT_SAFE_MIN = [  0.0,  30.0,   0.0,   0.0,   0.0,  30.0]
JOINT_SAFE_MAX = [180.0, 270.0, 180.0, 270.0, 180.0, 180.0]

# Home position (degrees) — matches arm_driver.py initialisation
JOINTS_HOME = [90.0, 90.0, 90.0, 0.0, 90.0, 30.0]

NUM_JOINTS = 6


class GamepadTeleop:
    def __init__(self):
        rospy.init_node("gamepad_teleop_node", anonymous=False)

        # ── Parameters (defaults match config/gamepad_config.yaml) ──────────
        self.joy_index    = int(rospy.get_param("~joy_index",    0))
        self.control_hz   = float(rospy.get_param("~control_hz", 30.0))
        self.speed_dps    = float(rospy.get_param("~speed_dps",  60.0))
        self.deadzone     = float(rospy.get_param("~deadzone",    0.08))
        self.move_time_ms = int(rospy.get_param("~move_time_ms", 100))

        # Axis mapping
        self.axis_j2 = int(rospy.get_param("~axis_j2", -1))  # -1 = disabled

        # Button mapping
        self.btn_start_rec     = int(rospy.get_param("~btn_start_rec",     0))
        self.btn_stop_rec      = int(rospy.get_param("~btn_stop_rec",      1))
        self.btn_discard       = int(rospy.get_param("~btn_discard",       2))
        self.btn_j4_pos        = int(rospy.get_param("~btn_j4_pos",        3))
        self.btn_j4_neg        = int(rospy.get_param("~btn_j4_neg",       -1))
        self.btn_gripper_close = int(rospy.get_param("~btn_gripper_close", 8))

        # Current joint targets (degrees), initialised to home
        self._joints = list(JOINTS_HOME)
        self._lock   = threading.Lock()

        # Button debounce state
        self._prev_btns: dict[int, bool] = {}

        # ── Publishers ───────────────────────────────────────────────────────
        self._target_pub = rospy.Publisher("TargetAngle", ArmJoint, queue_size=1)
        self._cmd_pub    = rospy.Publisher("/robot/cmd",  String,   queue_size=1)

        # ── Pygame joystick init ─────────────────────────────────────────────
        pygame.init()
        pygame.joystick.init()

        n_joy = pygame.joystick.get_count()
        if n_joy == 0:
            rospy.logfatal(
                "[GamepadTeleop] No joystick detected. "
                "Is the USB controller plugged in?")
            raise RuntimeError("No joystick found.")

        if self.joy_index >= n_joy:
            rospy.logwarn(
                "[GamepadTeleop] joy_index=%d but only %d joystick(s) found. "
                "Falling back to index 0.", self.joy_index, n_joy)
            self.joy_index = 0

        self._joystick = pygame.joystick.Joystick(self.joy_index)
        self._joystick.init()

        rospy.loginfo(
            "[GamepadTeleop] '%s'  axes=%d  btns=%d",
            self._joystick.get_name(),
            self._joystick.get_numaxes(),
            self._joystick.get_numbuttons())
        rospy.loginfo(
            "[GamepadTeleop] speed=%.0f deg/s  hz=%.0f",
            self.speed_dps, self.control_hz)
        rospy.loginfo(
            "  btn start=%d  stop=%d  discard=%d  j4+=%d  j4-=%s  grip-close=%d",
            self.btn_start_rec, self.btn_stop_rec, self.btn_discard,
            self.btn_j4_pos,
            str(self.btn_j4_neg) if self.btn_j4_neg >= 0 else "off",
            self.btn_gripper_close)
        rospy.loginfo(
            "  axis j0=0 j1=1 j2=%s j3=3 j5=5",
            str(self.axis_j2) if self.axis_j2 >= 0 else "off")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _apply_deadzone(self, value: float) -> float:
        if abs(value) < self.deadzone:
            return 0.0
        sign = 1.0 if value > 0.0 else -1.0
        return sign * (abs(value) - self.deadzone) / (1.0 - self.deadzone)

    def _trigger_to_unit(self, raw: float) -> float:
        """Map an axis to [0, 1] open magnitude (positive direction only)."""
        value = (raw + 1.0) / 2.0 if raw < 0.0 else raw
        return value if value > self.deadzone else 0.0

    def _axis(self, idx: int) -> float:
        return self._joystick.get_axis(idx) if 0 <= idx < self._joystick.get_numaxes() else 0.0

    def _button(self, idx: int) -> bool:
        return bool(self._joystick.get_button(idx)) if 0 <= idx < self._joystick.get_numbuttons() else False

    def _just_pressed(self, idx: int) -> bool:
        cur  = self._button(idx)
        prev = self._prev_btns.get(idx, False)
        self._prev_btns[idx] = cur
        return cur and not prev

    def _clamp_joints(self, joints: list) -> list:
        return [
            float(max(JOINT_SAFE_MIN[i], min(JOINT_SAFE_MAX[i], joints[i])))
            for i in range(NUM_JOINTS)
        ]

    def _publish_joints(self, joints: list, move_time_ms: int) -> None:
        msg          = ArmJoint()
        msg.joints   = [float(j) for j in joints]
        msg.run_time = move_time_ms
        self._target_pub.publish(msg)

    def _go_home(self) -> None:
        rospy.loginfo("[GamepadTeleop] → home")
        with self._lock:
            self._joints = list(JOINTS_HOME)
        self._publish_joints(JOINTS_HOME, move_time_ms=3000)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        rate = rospy.Rate(self.control_hz)
        dt   = 1.0 / self.control_hz

        while not rospy.is_shutdown():
            pygame.event.pump()

            # ── One-shot button events ────────────────────────────────────
            if self._just_pressed(self.btn_start_rec):
                rospy.loginfo("[GamepadTeleop] ● START recording")
                self._cmd_pub.publish(String(data="record"))

            if self._just_pressed(self.btn_stop_rec):
                rospy.loginfo("[GamepadTeleop] ■ STOP + SAVE")
                self._cmd_pub.publish(String(data="stop"))

            if self._just_pressed(self.btn_discard):
                rospy.logwarn("[GamepadTeleop] ✕ DISCARD + home reset")
                self._cmd_pub.publish(String(data="discard"))
                self._go_home()

            # ── Continuous joint deltas ───────────────────────────────────
            delta = [0.0] * NUM_JOINTS

            # j0 – base rotation      (left stick X)
            delta[0] =  self._apply_deadzone(self._axis(0))

            # j1 – shoulder           (left stick Y, inverted: north = joint up)
            delta[1] = -self._apply_deadzone(self._axis(1))

            # j2 – elbow twist  (axis_j2 when set in config, inverted like j1)
            if self.axis_j2 >= 0:
                delta[2] = -self._apply_deadzone(self._axis(self.axis_j2))

            # j3 – wrist pitch        (right stick Y; north = joint down)
            delta[3] =  self._apply_deadzone(self._axis(3))

            # j4 – twist joint   (btn_j4_pos held = positive, btn_j4_neg held = negative)
            if self._button(self.btn_j4_pos):
                delta[4] = 1.0
            elif self.btn_j4_neg >= 0 and self._button(self.btn_j4_neg):
                delta[4] = -1.0

            # j5 – gripper
            #   btn_gripper_close (btn 8) held → close
            #   axis 5 positive half only      → open
            #   Kept separate so releasing the close button never causes a
            #   spurious open (axis 5 may spring back to +1 on this controller).
            if self._button(self.btn_gripper_close):
                delta[5] = -1.0
            else:
                ax5 = self._axis(5)
                delta[5] = self._apply_deadzone(ax5) if ax5 > 0 else 0.0

            # ── Integrate and publish if any motion ───────────────────────
            if any(abs(d) > 0.0 for d in delta):
                with self._lock:
                    for i in range(NUM_JOINTS):
                        self._joints[i] += delta[i] * self.speed_dps * dt
                    self._joints = self._clamp_joints(self._joints)
                    snap = list(self._joints)
                self._publish_joints(snap, self.move_time_ms)

            rate.sleep()


if __name__ == "__main__":
    try:
        node = GamepadTeleop()
        node.run()
    except (RuntimeError, rospy.ROSInterruptException):
        pass
    finally:
        pygame.quit()
