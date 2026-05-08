#!/usr/bin/env python3
# encoding: utf-8
"""
keyboard_teleop.py — Teleoperate the Dofbot Pro via keyboard for
                     recording pick-and-place demonstrations.

Key layout
──────────
  Joint control (hold key to move continuously):

    Joint 0  base          a / d
    Joint 1  shoulder      w / s
    Joint 2  elbow         r / f
    Joint 3  wrist pitch   t / g
    Joint 4  wrist twist   y / h
    Joint 5  gripper       o / c    (o = open, c = close)

  Episode control (single press):

    [  — start recording
    ]  — stop + save episode (prompts for object label)
    \  — discard current episode + move arm to home
    z  — move arm to home (without discarding)
    p  — print current joint angles
    q  — quit

NOTE: the arm-enable command (rostopic pub /robot/cmd 'start') is separate
from recording.  Press [ to begin recording; it publishes 'record' not 'start'.

ROS parameters:
  ~control_hz   float  Command publish rate (default: 30)
  ~speed_dps    float  Max speed deg/s while key held (default: 60)
  ~move_time_ms int    arm_driver move-time per command ms (default: 100)
"""

import sys
import select
import termios
import threading
import tty

import rospy
from std_msgs.msg import String

from dofbot_pro_info.msg import ArmJoint

# ── Joint safety limits (degrees) ────────────────────────────────────────────
JOINT_SAFE_MIN = [  0.0,  30.0,   0.0,   0.0,   0.0,  30.0]
JOINT_SAFE_MAX = [180.0, 270.0, 180.0, 270.0, 180.0, 180.0]

# Soft close limit for gripper during data collection.
# Keeps demos below the mechanical hard-stop so recordings don't contain
# stall-force frames that teach the policy to over-squeeze.
# Override at launch: _gripper_soft_max_deg:=140
GRIPPER_SOFT_MAX_DEG = 140.0

JOINTS_HOME  = [90.0,  80.0, 45.0, 0.0, 90.0, 30.0]
JOINTS_PLACE = [180.0, 45.0, 60.0, 45.0, 90.0, 30.0]
NUM_JOINTS   = 6

# Key → (joint_index, direction)  direction: +1 or -1
KEY_JOINT_MAP = {
    "a": (0, -1), "d": (0, +1),  # j0 base
    "w": (1, +1), "s": (1, -1),  # j1 shoulder
    "r": (2, +1), "f": (2, -1),  # j2 elbow
    "t": (3, +1), "g": (3, -1),  # j3 wrist pitch
    "y": (4, +1), "h": (4, -1),  # j4 wrist twist
    "o": (5, -1), "c": (5, +1),  # j5 gripper (o=open, c=close)
}


class KeyboardTeleop:
    def __init__(self):
        rospy.init_node("keyboard_teleop_node", anonymous=False)

        self.control_hz   = float(rospy.get_param("~control_hz",   30.0))
        self.speed_dps    = float(rospy.get_param("~speed_dps",    60.0))
        self.move_time_ms = int(rospy.get_param("~move_time_ms",   100))
        self._gripper_soft_max = float(
            rospy.get_param("~gripper_soft_max_deg", GRIPPER_SOFT_MAX_DEG))

        self._joints = list(JOINTS_HOME)
        self._lock   = threading.Lock()

        # Set of keys currently held down
        self._held: set[str] = set()
        self._held_lock = threading.Lock()

        self._target_pub = rospy.Publisher("TargetAngle", ArmJoint, queue_size=1)
        self._cmd_pub    = rospy.Publisher("/robot/cmd",  String,   queue_size=1)

        rospy.loginfo("[KeyboardTeleop] Ready. speed=%.0f deg/s  hz=%.0f",
                      self.speed_dps, self.control_hz)
        self._print_help()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _print_help(self):
        rospy.loginfo(
            "\n"
            "  Joint keys (hold):\n"
            "    j0 base        a / d\n"
            "    j1 shoulder    w / s\n"
            "    j2 elbow       r / f\n"
            "    j3 wrist pitch t / g\n"
            "    j4 wrist twist y / h\n"
            "    j5 gripper     o (open) / c (close)\n"
            "\n"
            "  Episode:\n"
            "    [  start recording\n"
            "    ]  stop + save  (prompts for object label)\n"
            "    \\  discard + home\n"
            "    z  home\n"
            "    x  place position\n"
            "    p  print joints\n"
            "    q  quit\n"
        )

    def _clamp_joints(self, joints):
        clamped = [
            float(max(JOINT_SAFE_MIN[i], min(JOINT_SAFE_MAX[i], joints[i])))
            for i in range(NUM_JOINTS)
        ]
        clamped[5] = float(max(JOINT_SAFE_MIN[5], min(self._gripper_soft_max, clamped[5])))
        return clamped

    def _publish_joints(self, joints, move_time_ms):
        msg          = ArmJoint()
        msg.joints   = [float(j) for j in joints]
        msg.run_time = move_time_ms
        self._target_pub.publish(msg)

    def _go_home(self):
        rospy.loginfo("[KeyboardTeleop] → home")
        with self._lock:
            self._joints = list(JOINTS_HOME)
        self._publish_joints(JOINTS_HOME, move_time_ms=3000)
        
    def _go_place(self):
        rospy.loginfo("[KeyboardTeleop] → place position (gripper opens on arrival)")
        transit_time_ms = 3000
        with self._lock:
            # Keep current gripper value during transit so it doesn't open mid-air
            transit = list(JOINTS_PLACE)
            transit[5] = self._joints[5]
            self._joints = list(JOINTS_PLACE)
        self._publish_joints(transit, move_time_ms=transit_time_ms)

        def _open_gripper():
            rospy.sleep(transit_time_ms / 1000.0)
            rospy.loginfo("[KeyboardTeleop] → opening gripper")
            self._publish_joints(JOINTS_PLACE, move_time_ms=500)

        threading.Thread(target=_open_gripper, daemon=True).start()
    # ── Key reader thread ─────────────────────────────────────────────────────

    def _read_keys(self, old_settings):
        """
        Runs in a background thread.  Reads one character at a time from stdin
        without blocking the control loop.  Uses a simple protocol:
          - printable key → add to _held, sleep briefly, remove (simulates held)
          - special keys handled immediately
        """
        try:
            while not rospy.is_shutdown():
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if not rlist:
                    continue
                key = sys.stdin.read(1)
                if not key:
                    continue

                # ── Episode / control one-shots ───────────────────────────
                if key == "[":
                    rospy.loginfo("[KeyboardTeleop] ● START recording")
                    self._cmd_pub.publish(String(data="record"))
                elif key == "]":
                    # Temporarily restore normal terminal so we can prompt for the object label.
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    try:
                        sys.stdout.write("Object label (Enter to skip): ")
                        sys.stdout.flush()
                        label = sys.stdin.readline().strip()
                    finally:
                        tty.setcbreak(sys.stdin.fileno())
                    if label:
                        self._cmd_pub.publish(String(data=f"object: {label}"))
                        rospy.loginfo("[KeyboardTeleop] object label: '%s'", label)
                    rospy.loginfo("[KeyboardTeleop] ■ STOP + SAVE")
                    self._cmd_pub.publish(String(data="stop"))
                elif key == "\\":
                    rospy.logwarn("[KeyboardTeleop] ✕ DISCARD + home")
                    self._cmd_pub.publish(String(data="discard"))
                    self._go_home()
                elif key == "z":
                    self._go_home()
                elif key == "x":
                    self._go_place()
                elif key == "p":
                    with self._lock:
                        j = list(self._joints)
                    rospy.loginfo(
                        "[KeyboardTeleop] Joints (deg): %s",
                        "  ".join(f"j{i}={v:.1f}" for i, v in enumerate(j)))
                elif key == "q":
                    rospy.signal_shutdown("user quit")
                    break

                # ── Joint motion (hold simulation) ────────────────────────
                elif key in KEY_JOINT_MAP:
                    with self._held_lock:
                        self._held.add(key)

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    # ── Main control loop ─────────────────────────────────────────────────────

    def run(self):
        # Put terminal into cbreak mode (read one char at a time, no echo)
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

        reader = threading.Thread(target=self._read_keys,
                                  args=(old_settings,), daemon=True)
        reader.start()

        rate = rospy.Rate(self.control_hz)
        dt   = 1.0 / self.control_hz

        try:
            while not rospy.is_shutdown():
                with self._held_lock:
                    held_snap = set(self._held)
                    # Characters are instantaneous key presses (not true held),
                    # so clear them each tick.  The user holds the physical key
                    # which generates repeated characters from the OS.
                    self._held.clear()

                delta = [0.0] * NUM_JOINTS
                for key in held_snap:
                    if key in KEY_JOINT_MAP:
                        j_idx, direction = KEY_JOINT_MAP[key]
                        delta[j_idx] += direction

                if any(abs(d) > 0 for d in delta):
                    with self._lock:
                        for i in range(NUM_JOINTS):
                            if delta[i] != 0.0:
                                # Normalise so diagonal presses don't double speed
                                self._joints[i] += (
                                    (1.0 if delta[i] > 0 else -1.0)
                                    * self.speed_dps * dt
                                )
                        self._joints = self._clamp_joints(self._joints)
                        snap = list(self._joints)
                    self._publish_joints(snap, self.move_time_ms)

                rate.sleep()

        finally:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except Exception:
                pass


if __name__ == "__main__":
    try:
        node = KeyboardTeleop()
        node.run()
    except rospy.ROSInterruptException:
        pass
