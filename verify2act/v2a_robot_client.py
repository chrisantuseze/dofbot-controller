#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify2act/v2a_robot_client.py
==============================
Robot back-ends for the Verify2Act pipeline.  Both expose the same interface:

    client.capture_frame(timeout) -> BGR np.ndarray (640x480) | None
    client.execute_subtask(color, target, timeout) -> bool
    client.close()

RemoteRobotClient (roslibpy)
    Runs on ANY machine (workstation / laptop).  Talks to the Jetson through the
    rosbridge WebSocket, so the world model + critic + VLM can live on a GPU box
    while the Jetson only runs the ROS stack:

        Jetson:       roscore, arm_driver, camera, rosbridge_websocket,
                      lang_color_detect.py, lang_color_grasp.py
        Workstation:  python3 verify2act/v2a_pipeline.py --jetson_ip <jetson>

LocalRobotClient (rospy)
    Runs on the Jetson itself (needs a sourced ROS environment).
"""

import base64
import json
import logging
import threading
import time
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)
logging.getLogger("twisted").setLevel(logging.WARNING)   # twisted's info logging crashes on py3.8 logging

CAMERA_COMPRESSED = "/camera/color/image_raw/compressed"
CAMERA_RAW = "/camera/color/image_raw"
FRAME_SIZE = (640, 480)


def _decode_b64(data) -> bytes:
    return base64.b64decode(data) if isinstance(data, str) else bytes(data)


class RemoteRobotClient:
    """roslibpy back-end: camera + subtask execution over rosbridge."""

    def __init__(self, jetson_ip: str, port: int = 9090, connect_timeout: float = 15.0):
        import roslibpy

        self._roslibpy = roslibpy
        self._frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._done = threading.Event()
        self._result: dict = {}
        self._searching = threading.Event()   # detector acknowledged the command
        self._last_status: dict = {}

        logger.info("[Remote] Connecting to rosbridge ws://%s:%d ...", jetson_ip, port)
        self._ros = roslibpy.Ros(host=jetson_ip, port=port)
        self._ros.run()
        deadline = time.time() + connect_timeout
        while not self._ros.is_connected and time.time() < deadline:
            time.sleep(0.2)
        if not self._ros.is_connected:
            raise ConnectionError(f"Could not reach rosbridge at {jetson_ip}:{port}")

        # Prefer JPEG-compressed images: raw 640x480 base64-JSON is ~1.2 MB/frame.
        self._cam_sub = roslibpy.Topic(
            self._ros, CAMERA_COMPRESSED, "sensor_msgs/CompressedImage", throttle_rate=300
        )
        self._cam_sub.subscribe(self._on_compressed)
        self._raw_sub = None  # created lazily if the compressed topic is silent

        self._cmd_pub = roslibpy.Topic(self._ros, "/subtask_cmd", "std_msgs/String")
        self._cmd_pub.advertise()
        self._done_sub = roslibpy.Topic(self._ros, "/subtask_done", "std_msgs/String")
        self._done_sub.subscribe(self._on_done)
        self._status_sub = roslibpy.Topic(self._ros, "/detect_status", "std_msgs/String")
        self._status_sub.subscribe(self._on_status)

        time.sleep(1.0)  # let rosbridge wire up the subscriptions before first use
        logger.info("[Remote] Connected.")

    # ── callbacks (roslibpy thread; keep them short) ──────────────────────────

    def _set_frame(self, img: np.ndarray, stamp: Optional[float] = None):
        if img is None:
            return
        now = time.time()
        img = cv2.resize(img, FRAME_SIZE)
        with self._frame_lock:
            if stamp is not None:
                # Camera clock -> local clock offset, estimated as the smallest observed (arrival - stamp), i.e.
                # the stream's minimum latency; works even when the two machines' clocks differ.
                self._clock_offset = min(getattr(self, "_clock_offset", float("inf")), now - stamp)
                # A frame captured before capture_frame() was called (queued in rosbridge while the arm moved) is stale.
                if stamp + self._clock_offset < getattr(self, "_capture_after", 0.0) - 0.05:
                    self._stale_dropped = getattr(self, "_stale_dropped", 0) + 1
                    return
            self._frame = img

    @staticmethod
    def _stamp(msg: dict) -> Optional[float]:
        try:
            st = msg["header"]["stamp"]
            t = float(st["secs"]) + float(st["nsecs"]) * 1e-9
            return t if t > 0 else None
        except Exception:
            return None

    def _on_compressed(self, msg: dict):
        try:
            buf = np.frombuffer(_decode_b64(msg["data"]), dtype=np.uint8)
            self._set_frame(cv2.imdecode(buf, cv2.IMREAD_COLOR), self._stamp(msg))
        except Exception as e:
            logger.debug("[Remote] bad compressed frame: %s", e)

    def _on_raw(self, msg: dict):
        try:
            h, w, enc = msg["height"], msg["width"], msg["encoding"]
            img = np.frombuffer(_decode_b64(msg["data"]), dtype=np.uint8).reshape(h, w, 3)
            if enc == "rgb8":
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            self._set_frame(img.copy(), self._stamp(msg))
        except Exception as e:
            logger.debug("[Remote] bad raw frame: %s", e)

    def _on_done(self, msg: dict):
        try:
            self._result = json.loads(msg["data"])
        except Exception:
            self._result = {"status": msg.get("data", "unknown")}
        self._done.set()

    def _on_status(self, msg: dict):
        try:
            self._last_status = json.loads(msg["data"])
        except Exception:
            return
        if self._last_status.get("status") == "searching":
            self._searching.set()

    # ── public API ────────────────────────────────────────────────────────────

    def capture_frame(self, timeout: float = 8.0) -> Optional[np.ndarray]:
        """Return the newest camera frame (BGR, 640x480) or None on timeout."""
        with self._frame_lock:
            self._frame = None          # force a *fresh* frame, not a stale one
            self._capture_after = time.time()   # ...and not one captured before this call (see _set_frame)
            self._stale_dropped = 0
        deadline = time.time() + timeout
        fallback_at = time.time() + 2.0
        while time.time() < deadline:
            with self._frame_lock:
                if self._frame is not None:
                    if self._stale_dropped:
                        logger.info("[Remote] dropped %d stale queued frame(s) before a fresh one", self._stale_dropped)
                    return self._frame.copy()
            if self._raw_sub is None and time.time() > fallback_at:
                logger.warning("[Remote] No compressed frames; falling back to raw topic.")
                self._raw_sub = self._roslibpy.Topic(
                    self._ros, CAMERA_RAW, "sensor_msgs/Image", throttle_rate=500
                )
                self._raw_sub.subscribe(self._on_raw)
            time.sleep(0.05)
        return None

    def execute_subtask(self, color: str, target: str = "left_bin", timeout: float = 45.0,
                        action: str = "pick_place", base_color: Optional[str] = None) -> bool:
        # place_on / place_at: the detector must look for the BASE (reference) block, `held` is the block in the gripper
        payload = json.dumps({"action": action, "color": base_color if action in ("place_on", "place_at") else color,
                              "held": color, "target": target})
        self._done.clear()
        self._searching.clear()
        self._result = {}

        # A single publish right after advertise can be dropped; retry until the
        # detector reports "searching" (proof the command reached the Jetson).
        for attempt in range(1, 4):
            logger.info("[Remote] subtask_cmd -> %s (try %d)", payload, attempt)
            self._cmd_pub.publish(self._roslibpy.Message({"data": payload}))
            if self._searching.wait(timeout=3.0):
                break
        else:
            logger.error("[Remote] Command not acknowledged by lang_color_detect "
                         "(are lang_color_detect.py / lang_color_grasp.py running?).")
            return False

        if not self._done.wait(timeout=timeout):
            logger.error("[Remote] Timed out after %.0fs (last detect status: %s). "
                         "Block probably not visible.", timeout, self._last_status)
            return False
        ok = self._result.get("status") == "success"
        if not ok:
            logger.error("[Remote] Subtask failed: %s", self._result)
        return ok

    def close(self):
        for t in (self._cam_sub, self._raw_sub, self._done_sub, self._status_sub):
            try:
                if t is not None:
                    t.unsubscribe()
            except Exception:
                pass
        try:
            self._cmd_pub.unadvertise()
        except Exception:
            pass
        if self._ros.is_connected:
            self._ros.terminate()


class LocalRobotClient:
    """rospy back-end for running the whole pipeline on the Jetson."""

    def __init__(self):
        import rospy
        from lang_color_grasp import LanguageGraspClient  # scripts/Color on sys.path

        self._rospy = rospy
        self._grasp = LanguageGraspClient()

    def capture_frame(self, timeout: float = 8.0) -> Optional[np.ndarray]:
        try:
            from sensor_msgs.msg import Image
            from cv_bridge import CvBridge

            msg = self._rospy.wait_for_message(CAMERA_RAW, Image, timeout=timeout)
            return cv2.resize(CvBridge().imgmsg_to_cv2(msg, "bgr8"), FRAME_SIZE)
        except Exception as e:
            logger.warning("[Local] camera capture failed: %s", e)
            return None

    def execute_subtask(self, color: str, target: str = "left_bin", timeout: float = 45.0,
                        action: str = "pick_place", base_color: Optional[str] = None) -> bool:
        return self._grasp.execute_subtask(color=color, target=target, timeout=timeout,
                                           action=action, base_color=base_color)

    def close(self):
        pass
