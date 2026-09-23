"""
verify2act/remote/proxies.py
============================
Jetson-side stand-ins for the world model and critic.  They expose the same methods as
WorldModelStub / CriticModel, but forward each call to the server (v2a_server.py) over
rosbridge and wait for the reply, so the pipeline code is identical for local and remote models.
"""

import json
import logging
import threading
import uuid
from types import SimpleNamespace
from typing import Optional

import numpy as np

from verify2act.remote.protocol import (MSG_TYPE, REQUEST_TOPIC, RESPONSE_TOPIC, decode_image, encode_image)

logger = logging.getLogger(__name__)


class ServerLink:
    """One request/response channel over an existing roslibpy.Ros connection."""

    def __init__(self, ros, timeout: float = 60.0):
        import roslibpy
        self._msg = roslibpy.Message
        self._timeout = timeout
        self._pending = {}
        self._lock = threading.Lock()
        self._pub = roslibpy.Topic(ros, REQUEST_TOPIC, MSG_TYPE)
        self._pub.advertise()
        self._sub = roslibpy.Topic(ros, RESPONSE_TOPIC, MSG_TYPE)
        self._sub.subscribe(self._on_response)

    def _on_response(self, msg: dict):
        try:
            r = json.loads(msg["data"])
        except Exception:
            return
        with self._lock:
            slot = self._pending.get(r.get("id"))
        if slot:
            slot["reply"] = r
            slot["event"].set()

    def call(self, op: str, timeout: Optional[float] = None, **payload) -> dict:
        rid = uuid.uuid4().hex[:12]
        slot = {"event": threading.Event(), "reply": None}
        with self._lock:
            self._pending[rid] = slot
        try:
            self._pub.publish(self._msg({"data": json.dumps({"id": rid, "op": op, **payload})}))
            if not slot["event"].wait(timeout or self._timeout):
                raise TimeoutError(f"No reply to '{op}' from the world-model/critic server "
                                   f"(is v2a_server.py running and connected to this rosbridge?)")
            reply = slot["reply"]
            if not reply.get("ok", False):
                raise RuntimeError(f"Server error on '{op}': {reply.get('error')}")
            return reply
        finally:
            with self._lock:
                self._pending.pop(rid, None)

    def wait_for_server(self, attempts: int = 10) -> None:
        for _ in range(attempts):
            try:
                self.call("ping", timeout=2.0)
                return
            except TimeoutError:
                continue
        raise ConnectionError("World-model/critic server did not answer 'ping'. Start it with:\n"
                              "  python3 verify2act/remote/v2a_server.py --jetson_ip <JETSON_IP>")

    def close(self):
        for t in (self._sub, self._pub):
            try:
                t.unsubscribe() if t is self._sub else t.unadvertise()
            except Exception:
                pass


def evaluate_plan_remote(link: ServerLink, session: str, actions, obs, goal, s_init, theta_c, theta_p, confidence,
                         max_requery, inject_fault: bool = False) -> dict:
    """One round trip: the server imagines + scores the whole plan. Returns the same dict as evaluate_plan()."""
    r = link.call("evaluate_plan", session=session, image=encode_image(obs), goal=goal, actions=list(actions),
                  theta_c=theta_c, theta_p=theta_p, confidence=confidence, max_requery=max_requery,
                  fault=bool(inject_fault), image_init=encode_image(s_init) if s_init is not None else None)
    r["frames"] = [decode_image(f) for f in r.get("frames", [])] or [obs]
    r.setdefault("goal", None)
    return r


class RemoteWorldModel:
    """Only used for reset(): plan evaluation goes through evaluate_plan_remote()."""
    def __init__(self, link: ServerLink):
        self.link = link

    def reset(self, session: str):
        self.link.call("reset", session=session)

    def create_synthetic_scene(self) -> np.ndarray:   # offline fallback only; needs no server
        from verify2act.v2a_world_model import WorldModelStub
        return WorldModelStub().create_synthetic_scene()


class RemoteCritic:
    """Goal-head score of a real frame ('is the task done?')."""
    def __init__(self, link: ServerLink):
        self.link = link

    def goal_sim_with_uncertainty(self, frame, language_goal, initial_frame=None, executed=None):
        r = self.link.call("goal_check", image=encode_image(frame), goal=language_goal,
                           image_init=encode_image(initial_frame) if initial_frame is not None else None)
        return r["mean"], r["std"], r["reason"]
