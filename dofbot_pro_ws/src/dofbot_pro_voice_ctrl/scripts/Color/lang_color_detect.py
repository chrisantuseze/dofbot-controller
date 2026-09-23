#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lang_color_detect.py
====================
Standalone color detection node for DOFBOT Pro, compatible with language-guided
and Verify2Act multi-step workflows.

Accepts target color via:
  - /voice_result (std_msgs/Int8): 7=red, 8=green, 9=blue, 10=yellow
  - /target_color (std_msgs/String): "red", "green", "blue", "yellow"

Publishes:
  - /xyz (dofbot_pro_info/Position): pixel x, y and camera depth z (m)
  - /detect_status (std_msgs/String): JSON status updates

Subscribes to:
  - /grasp_done or /subtask_done: resets detection for the next subtask
"""

import os
import sys
import time
import math
import json
from pathlib import Path

_HEADLESS = (os.environ.get("DISPLAY", "") == "")
if _HEADLESS:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import rospy
import numpy as np
import cv2 as cv
from sensor_msgs.msg import Image
import message_filters
from std_msgs.msg import Float32, Bool, Int8, String
from cv_bridge import CvBridge
import rospkg

# Import astra_common from voice ctrl directory
try:
    pkg_path = rospkg.RosPack().get_path("dofbot_pro_voice_ctrl")
    scripts_color_path = os.path.join(pkg_path, "scripts", "Color")
    if scripts_color_path not in sys.path:
        sys.path.insert(0, scripts_color_path)
    from astra_common import color_detect, read_HSV
except Exception as e:
    sys.stderr.write(f"[lang_color_detect] Warning: could not import astra_common directly: {e}\n")

from dofbot_pro_info.msg import Position, ArmJoint

COLOR_MAP_ID_TO_NAME = {
    7: "red",
    8: "green",
    9: "blue",
    10: "yellow"
}

COLOR_MAP_NAME_TO_ID = {v: k for k, v in COLOR_MAP_ID_TO_NAME.items()}


class LangColorDetectNode:
    def __init__(self):
        rospy.init_node("lang_color_detect", anonymous=False)

        self.rgb_bridge = CvBridge()
        self.depth_bridge = CvBridge()

        # Calibration files
        hsv_dir = os.path.join(rospkg.RosPack().get_path("dofbot_pro_voice_ctrl"), "scripts", "Color")
        self.hsv_paths = {
            "red": os.path.join(hsv_dir, "red_colorHSV.text"),
            "green": os.path.join(hsv_dir, "green_colorHSV.text"),
            "blue": os.path.join(hsv_dir, "blue_colorHSV.text"),
            "yellow": os.path.join(hsv_dir, "yellow_colorHSV.text"),
        }

        self.color_detector = color_detect()
        self.target_color = "red"
        self.hsv_range = ()
        self.track_state = "init"
        self.pub_pos_flag = False

        self.cx = 0
        self.cy = 0
        self.circle_r = 0
        self.pr_time = time.time()

        # ROS Communications
        self.pub_xyz = rospy.Publisher("xyz", Position, queue_size=1)
        self.pub_status = rospy.Publisher("detect_status", String, queue_size=5)
        self.pub_subtask_done = rospy.Publisher("subtask_done", String, queue_size=1)

        # Trigger inputs
        self.sub_voice = rospy.Subscriber("voice_result", Int8, self.on_voice_result, queue_size=1)
        self.sub_target_color = rospy.Subscriber("target_color", String, self.on_target_color, queue_size=1)

        # Reset triggers
        self.sub_grasp_done = rospy.Subscriber("grasp_done", Bool, self.on_grasp_done, queue_size=1)
        self.sub_subtask_done = rospy.Subscriber("subtask_done", String, self.on_subtask_done, queue_size=1)

        # Image streams
        self.sub_rgb = message_filters.Subscriber("/camera/color/image_raw", Image)
        self.sub_depth = message_filters.Subscriber("/camera/depth/image_raw", Image)
        self.sync = message_filters.ApproximateTimeSynchronizer([self.sub_rgb, self.sub_depth], 10, 0.5)
        self.sync.registerCallback(self.image_callback)

        # Set exposure
        os.system("rosservice call /camera/set_color_exposure 50 2>/dev/null || true")

        rospy.loginfo("[lang_color_detect] Node initialized. Ready for subtasks.")

    def set_target(self, color_name: str):
        color_name = color_name.lower().strip()
        if color_name not in self.hsv_paths:
            rospy.logwarn(f"[lang_color_detect] Unknown color requested: '{color_name}'")
            return False

        self.target_color = color_name
        hsv_file = self.hsv_paths[color_name]
        if os.path.exists(hsv_file):
            self.hsv_range = read_HSV(hsv_file)
            rospy.loginfo(f"[lang_color_detect] Loaded HSV for '{color_name}' from {hsv_file}: {self.hsv_range}")
        else:
            rospy.logerr(f"[lang_color_detect] Calibration file not found: {hsv_file}")
            return False

        self.track_state = "identify"
        self.pub_pos_flag = True
        self.search_start = time.time()
        self.cx, self.cy, self.circle_r = 0, 0, 0
        self._publish_status("searching", {"color": self.target_color})
        return True

    def on_voice_result(self, msg: Int8):
        color_name = COLOR_MAP_ID_TO_NAME.get(msg.data)
        if color_name:
            rospy.loginfo(f"[lang_color_detect] Voice command ID {msg.data} -> Target: {color_name}")
            self.set_target(color_name)
        else:
            rospy.logwarn(f"[lang_color_detect] Received unmapped voice ID: {msg.data}")

    def on_target_color(self, msg: String):
        rospy.loginfo(f"[lang_color_detect] Target color message: '{msg.data}'")
        self.set_target(msg.data)

    def on_grasp_done(self, msg: Bool):
        if msg.data:
            self._reset_detection(reason="grasp_done")

    def on_subtask_done(self, msg: String):
        self._reset_detection(reason=f"subtask_done: {msg.data}")

    def _reset_detection(self, reason: str):
        self.pub_pos_flag = False
        self.track_state = "init"
        self.cx = 0
        self.cy = 0
        self.circle_r = 0
        rospy.loginfo(f"[lang_color_detect] Reset detection to standby ({reason}).")
        self._publish_status("idle", {"reason": reason})

    def _publish_status(self, status: str, extra: dict = None):
        payload = {"status": status, "target_color": self.target_color, "timestamp": time.time()}
        if extra:
            payload.update(extra)
        self.pub_status.publish(String(data=json.dumps(payload)))

    def image_callback(self, rgb_msg: Image, depth_msg: Image):
        try:
            rgb_image = self.rgb_bridge.imgmsg_to_cv2(rgb_msg, "bgr8")
            rgb_image = cv.resize(rgb_image, (640, 480))

            depth_image = self.depth_bridge.imgmsg_to_cv2(depth_msg, "32FC1")
            depth_image = cv.resize(depth_image, (640, 480)).astype(np.float32)
        except Exception as e:
            rospy.logerr_throttle(5.0, f"[lang_color_detect] CV bridge error: {e}")
            return

        # Give up on a block that can't be found, so a late lock-on never starts a pick after the caller moved on.
        if self.pub_pos_flag and time.time() - getattr(self, "search_start", time.time()) > rospy.get_param("~search_timeout", 25.0):
            rospy.logwarn(f"[lang_color_detect] '{self.target_color}' not found within the search timeout; giving up.")
            self._reset_detection(reason="not_found")
            self.pub_subtask_done.publish(String(data=json.dumps(
                {"status": "error", "error": f"{self.target_color} block not found", "timestamp": time.time()})))
            return

        if self.track_state == "identify" and len(self.hsv_range) != 0:
            self.cx, self.cy, self.circle_r = self._find_blob(rgb_image)

            # Filter valid circle radius and ROI bounds (table workspace)
            # The edge margin rejects false blobs at the frame border (seen at y=449-469 with a wrong depth,
            # which sent the arm to the wrong place). Real blocks on the sheet sit well inside it.
            if self.circle_r > 15 and 20 < self.cx < 620 and 20 < self.cy < 420:
                pos = Position()
                pos.x = float(self.cx)
                pos.y = float(self.cy)

                # 7x7 patch depth sampling for noise suppression
                ix, iy = int(self.cx), int(self.cy)
                patch = depth_image[max(0, iy - 3):min(480, iy + 4), max(0, ix - 3):min(640, ix + 4)]
                valid_depths = patch[patch > 0]
                if len(valid_depths) > 0:
                    pos.z = float(np.median(valid_depths)) / 1000.0
                else:
                    pos.z = float(depth_image[iy, ix]) / 1000.0

                if self.pub_pos_flag:
                    # Save debug frame
                    self._save_debug_image(rgb_image, pos)

                    if pos.z <= 0.0:
                        rospy.logwarn_throttle(2.0, f"[lang_color_detect] Target at ({pos.x:.0f}, {pos.y:.0f}) has depth 0.0m (too close)!")
                    else:
                        rospy.loginfo(f"[lang_color_detect] Target confirmed at pixel=({pos.x:.1f}, {pos.y:.1f}), depth={pos.z:.3f}m")
                        self.pub_xyz.publish(pos)
                        self.pub_pos_flag = False  # Single-shot latch
                        self._publish_status("locked", {"x": pos.x, "y": pos.y, "z": pos.z})

    def _find_blob(self, rgb_image):
        """Same as color_detect.object_follow (largest blob -> minAreaRect -> enclosing circle), except that red
        also takes hue 0-8 (not 10: the wooden table is hue 9-14): red wraps around the hue circle and the calibrated 160-180 range alone caught only
        speckles of the block (centre off by up to ~2 cm)."""
        hsv = cv.cvtColor(rgb_image, cv.COLOR_BGR2HSV)
        lo, hi = self.hsv_range
        mask = cv.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
        if self.target_color == "red":
            mask |= cv.inRange(hsv, np.array((0, lo[1], lo[2]), np.uint8), np.array((8, hi[1], hi[2]), np.uint8))
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, cv.getStructuringElement(cv.MORPH_RECT, (5, 5)))
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)[-2:]
        if not contours:
            return 0, 0, 0
        box = np.int0(cv.boxPoints(cv.minAreaRect(max(contours, key=cv.contourArea))))
        (x, y), r = cv.minEnclosingCircle(box)
        return int(x), int(y), int(r)

    def _save_debug_image(self, rgb_image: np.ndarray, pos: Position):
        try:
            debug_dir = Path("/home/jetson/echris/dofbot-controller/debug_output")
            debug_dir.mkdir(parents=True, exist_ok=True)
            dbg = rgb_image.copy()
            cv.circle(dbg, (int(pos.x), int(pos.y)), int(self.circle_r), (0, 255, 0), 2)
            cv.circle(dbg, (int(pos.x), int(pos.y)), 5, (0, 0, 255), -1)
            label = f"{self.target_color}: x={pos.x:.0f} y={pos.y:.0f} z={pos.z:.3f}m"
            cv.putText(dbg, label, (15, 35), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv.imwrite(str(debug_dir / "last_detection.jpg"), dbg)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        node = LangColorDetectNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
