"""
verify2act/remote/protocol.py
=============================
Wire format between the Jetson (orchestrator + robot) and the world-model / critic server.

Transport: rosbridge topics of type std_msgs/String carrying JSON; images are base64 JPEG.
    /v2a/request   Jetson  -> server   {"id", "op", ...}
    /v2a/response  server  -> Jetson   {"id", "ok", "error"?, ...}

ops
    ping
    reset          {session}                       clear world-model state for a new episode
    evaluate_plan  {session, image, goal, actions[], theta_c, theta_p, confidence, max_requery, fault?, image_init?}
                   -> {accepted, steps[{horizon, action, mean, std, decision, reason}],
                       goal{mean, std, decision, reason}|null, requeries, temporal_rejections,
                       goal_rejections, ctx{reason, failed_step, temporal_scores, proximity}, frames[]?}
                   The server runs the whole imagine + critic loop (latent world-model state never leaves it).
                   `frames` (b64 JPEG of S_0..S_H) is optional: a latent world model needs a decoder to provide it.
    goal_check     {image, goal, image_init?}  -> {mean, std, reason}
                   Goal-head score of a REAL camera frame (is the task done?).
"""

import base64

import cv2
import numpy as np

REQUEST_TOPIC = "/v2a/request"
RESPONSE_TOPIC = "/v2a/response"
MSG_TYPE = "std_msgs/String"


def encode_image(img: np.ndarray, quality: int = 92) -> str:
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ValueError("JPEG encoding failed")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def decode_image(b64: str) -> np.ndarray:
    return cv2.imdecode(np.frombuffer(base64.b64decode(b64), np.uint8), cv2.IMREAD_COLOR)
