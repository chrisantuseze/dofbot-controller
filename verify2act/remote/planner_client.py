"""
verify2act/remote/planner_client.py
===================================
Client for the lab-PC Verify2Act plan server (research repo, branch main-wm: verify2act/robot/server.py).
One `plan` round trip = VLM proposal + world-model imagination + critic gating + reflect/replan, all on the server.

    Lab PC:  python -m verify2act.robot.server --jetson-ip <JETSON_IP>
"""
import logging
import re
from typing import List, Optional

import numpy as np

from verify2act.remote.protocol import encode_image
from verify2act.remote.proxies import ServerLink
from verify2act.v2a_goal import parse_relative, parse_step
from verify2act.v2a_vlm_planner import COLOR_CODE_MAP, Subtask

logger = logging.getLogger(__name__)

PLAN_REPLY_TIMEOUT_S = 600.0
PING_REPLY_TIMEOUT_S = 5.0

# Effective server-side values (verify2act/robot/server.py defaults); the Jetson's --theta_*/--max_* flags are ignored.
SERVER_SETTINGS = {"theta_c": 0.5, "theta_p": 0.05, "max_replans": 2, "max_requery": 2}

# Subtask vocabulary shared with the server (research repo: verify2act/robot/prompts.py). One subtask = one world-model
# horizon = one complete pick-and-place that ends with nothing held: the arm cannot hold a block while the next
# subtask is planned and verified, so there is no bare "pick" / "place".
_C = "(red|green|blue|yellow)"
_VALID = [re.compile(p) for p in (
    rf"^pick and place {_C} block into the bin$",
    rf"^pick and place {_C} block on {_C} block$",
    rf"^pick and place {_C} block to the (left|right) of {_C} block$",
)]


def is_valid_subtask(text: str) -> bool:
    return any(p.match(text) for p in _VALID)


def subtask_from_text(text: str) -> Subtask:
    """Server subtask string -> Subtask for _execute(). Raises ValueError outside the vocabulary."""
    text = " ".join(text.strip().lower().split())
    if not is_valid_subtask(text):
        raise ValueError(f"subtask outside the robot vocabulary: {text!r}")
    kind, color, base = parse_step(text)
    if base == color:
        raise ValueError(f"subtask places a block relative to itself: {text!r}")
    target = {"pick_place": "left_bin", "stack": f"on_{base}"}.get(kind) or parse_relative(text)[1]   # rearrange: left_of | right_of
    return Subtask(action_text=text, color=color, color_id=COLOR_CODE_MAP[color], target_placement=target,
                   kind=kind, base_color=base)


class PlanServerClient:
    """Uses the rosbridge connection the RemoteRobotClient already holds."""

    def __init__(self, ros):
        self.link = ServerLink(ros, timeout=PLAN_REPLY_TIMEOUT_S)

    def wait_for_server(self, attempts: int = 60) -> None:
        try:
            self.link.wait_for_server(attempts=attempts)      # pings every ~2 s
        except ConnectionError:
            raise ConnectionError("Verify2Act plan server did not answer 'ping'. On the lab PC run:\n"
                                  "  python -m verify2act.robot.server --jetson-ip <JETSON_IP>\n"
                                  "and wait for 'Ready: listening on /v2a/request' (~4 min model load).") from None

    def reset(self, session: str) -> None:
        self.link.call("reset", timeout=PING_REPLY_TIMEOUT_S, session=session)

    def plan(self, session: str, frame_bgr: np.ndarray, goal: str, history: List[str],
             obj_labels: Optional[List[str]] = None, horizon: Optional[int] = None) -> dict:
        payload = {"session": session, "image": encode_image(frame_bgr), "goal": goal, "history": list(history)}
        if obj_labels:
            payload["obj_labels"] = list(obj_labels)
        if horizon:
            payload["horizon"] = int(horizon)
        return self.link.call("plan", timeout=PLAN_REPLY_TIMEOUT_S, **payload)   # RuntimeError / TimeoutError on failure

    def close(self) -> None:
        self.link.close()
