#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify2act/remote/v2a_server.py
===============================
World-model + critic server.  Runs on a GPU machine, NOT on the Jetson.

It connects OUT to the Jetson's rosbridge (same pattern as unveiler_inference_server.py, so the Jetson
needs no extra open ports), listens on /v2a/request, and answers on /v2a/response.

    Jetson:   roscore, arm_driver, camera, rosbridge, lang_color_detect.py, lang_color_grasp.py,
              python3 verify2act/v2a_session.py --jetson_ip 127.0.0.1 --wm_server ...
    Server:   python3 verify2act/remote/v2a_server.py --jetson_ip <JETSON_IP>

Backends
    stub  colour-blob world model + critic (default; the same stubs the local pipeline uses)
    To serve the research models, add a class with the same methods as StubBackend
    (reset / evaluate_plan / goal_check) that wraps LatentWorldModel + DINOv2DualHeadCritic and select it
    with --backend.
"""

import argparse
import json
import logging
import sys
import threading
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import roslibpy

from verify2act.remote.protocol import MSG_TYPE, REQUEST_TOPIC, RESPONSE_TOPIC, decode_image, encode_image

logging.getLogger("twisted").setLevel(logging.WARNING)
logger = logging.getLogger("v2a_server")


class StubBackend:
    """Stateful per session (the world model remembers the block it 'picked')."""

    def __init__(self, force_uncertain: int = 0):
        from verify2act.v2a_critic import CriticModel
        from verify2act.v2a_world_model import WorldModelStub
        self._wm_cls = WorldModelStub
        self.critic = CriticModel(force_uncertain=force_uncertain)
        self.sessions = {}

    def _wm(self, session: str):
        return self.sessions.setdefault(session, self._wm_cls())

    def reset(self, session: str):
        self.sessions[session] = self._wm_cls()

    def evaluate_plan(self, session, image, goal, actions, theta_c, theta_p, confidence, max_requery, fault, image_init):
        from verify2act.v2a_plan_eval import evaluate_plan
        fire = {"v": bool(fault)}
        def inject():
            v, fire["v"] = fire["v"], False
            return v
        return evaluate_plan(self._wm(session), self.critic, actions, image, goal, image_init, theta_c, theta_p,
                             confidence, max_requery, inject_fault=inject, log=logger.info)

    def goal_check(self, image, goal, image_init):
        return self.critic.goal_sim_with_uncertainty(image, goal, image_init)


BACKENDS = {"stub": StubBackend}


class Server:
    def __init__(self, args):
        self.backend = BACKENDS[args.backend](force_uncertain=1 if args.simulate_uncertainty else 0) \
            if args.backend == "stub" else BACKENDS[args.backend]()
        logger.info("Connecting to rosbridge ws://%s:%d ...", args.jetson_ip, args.port)
        self.ros = roslibpy.Ros(host=args.jetson_ip, port=args.port)
        self.ros.run()
        deadline = time.time() + 15
        while not self.ros.is_connected and time.time() < deadline:
            time.sleep(0.2)
        if not self.ros.is_connected:
            raise ConnectionError("Could not reach rosbridge on the Jetson")
        self.pub = roslibpy.Topic(self.ros, RESPONSE_TOPIC, MSG_TYPE)
        self.pub.advertise()
        self.sub = roslibpy.Topic(self.ros, REQUEST_TOPIC, MSG_TYPE)
        self.sub.subscribe(self.on_request)
        self.lock = threading.Lock()   # one model call at a time (GPU)
        logger.info("Ready: listening on %s", REQUEST_TOPIC)

    def on_request(self, msg: dict):
        # roslibpy callbacks run on the websocket thread; do the work elsewhere so pings stay responsive.
        threading.Thread(target=self.handle, args=(msg["data"],), daemon=True).start()

    def handle(self, raw: str):
        req = json.loads(raw)
        rid, op = req.get("id"), req.get("op")
        t0 = time.time()
        try:
            with self.lock:
                out = self.dispatch(op, req)
            reply = {"id": rid, "ok": True, **out}
        except Exception as e:
            logger.exception("op %s failed", op)
            reply = {"id": rid, "ok": False, "error": f"{type(e).__name__}: {e}"}
        self.pub.publish(roslibpy.Message({"data": json.dumps(reply)}))
        logger.info("%-8s %.2fs", op, time.time() - t0)

    def dispatch(self, op: str, r: dict) -> dict:
        b = self.backend
        if op == "ping":
            return {}
        if op == "reset":
            b.reset(r["session"])
            return {}
        if op == "evaluate_plan":
            init = decode_image(r["image_init"]) if r.get("image_init") else None
            out = b.evaluate_plan(r["session"], decode_image(r["image"]), r["goal"], r["actions"], r["theta_c"],
                                  r["theta_p"], r["confidence"], r["max_requery"], r.get("fault", False), init)
            frames = out.pop("frames", [])
            out["frames"] = [encode_image(f) for f in frames] if r.get("want_frames", True) else []
            return out
        if op == "goal_check":
            init = decode_image(r["image_init"]) if r.get("image_init") else None
            m, s, why = b.goal_check(decode_image(r["image"]), r["goal"], init)
            return {"mean": float(m), "std": float(s), "reason": why}
        raise ValueError(f"unknown op '{op}'")

    def run(self):
        try:
            while self.ros.is_connected:
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass
        finally:
            self.ros.terminate()


def main():
    ap = argparse.ArgumentParser(description="Verify2Act world-model + critic server")
    ap.add_argument("--jetson_ip", required=True)
    ap.add_argument("--port", type=int, default=9090)
    ap.add_argument("--backend", choices=list(BACKENDS), default="stub")
    ap.add_argument("--simulate_uncertainty", action="store_true", help="stub critic is uncertain once (tests requery)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    Server(args).run()


if __name__ == "__main__":
    main()
