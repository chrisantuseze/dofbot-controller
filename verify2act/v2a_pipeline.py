#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify2act/v2a_pipeline.py
==========================
Verify2Act on the DOFBOT Pro: the receding-horizon loop of the research repo
(verify2act/pipeline/inference.py :: run_episode), driving the real arm.

Each timestep t:
  1. observe        real camera frame
  2. propose        VLM planner proposes a plan (list of subtask horizons)
  3. imagine+critic per horizon: world model imagines S_{t+1}; temporal head (theta_c) gates it
                    -> continue | requery (re-imagine); after the last horizon the goal head
                    (theta_p) judges the final imagined frame against the language goal
                    -> continue | requery (re-roll whole plan) | reflect
  4. reflect        critic diagnosis goes back to the VLM which revises the plan (budget: max_replans)
  5. execute        the verified plan runs on the arm (full_plan, or step_by_step = first action only)
  6. re-observe     the real frame is checked against the goal (goal head); done, or plan again

World model / critic / VLM here are stubs with the research repo's interfaces; they can run on a
GPU workstation while the Jetson only runs ROS (see --jetson_ip):
    Jetson:       roscore, arm_driver, camera, rosbridge, lang_color_detect.py, lang_color_grasp.py
    Workstation:  python3 verify2act/v2a_pipeline.py --task task1a --jetson_ip <JETSON_IP>
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

# Ensure parent root and Color scripts are in sys.path
_ROOT = Path(__file__).resolve().parent.parent
_COLOR_DIR = _ROOT / "dofbot_pro_ws" / "src" / "dofbot_pro_voice_ctrl" / "scripts" / "Color"
for p in [str(_ROOT), str(_COLOR_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from verify2act.v2a_world_model import WorldModelStub
from verify2act.v2a_critic import CriticModel
from verify2act.v2a_decisions import check_rollout_consistency, decide_from_proximity
from verify2act.v2a_plan_eval import evaluate_plan
from verify2act.v2a_vlm_planner import VLMPlanner, Subtask

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Verify2Act")

TASK_PRESETS = {
    "task1a": "Put the blue block and the yellow block into the bin",
    "task1b": "Clear all cool-colored blocks into the bin and leave the yellow block",
    "task1c": "Clear all warm-colored blocks into the bin and leave the green block",
    "task1d": "Put the red block, the green block and the blue block into the bin except the yellow block",
    # Rearrangement: the moved block is set down ~place_gap (7 cm) centre-to-centre beside the reference block.
    # Scene setup: leave >= 10 cm of empty sheet on that side of the reference block, and keep it left of
    # image x ~440 px (world x <= +3 cm), where placements are known to land ~2 cm short.
    "task2a": "Put the red block to the left of the blue block",
    "task2b": "Put the green block to the right of the yellow block",
    "task3a": "Stack the blue block on top of the yellow block",
}

BANNER = "=" * 72


def print_banner(text: str):
    print(f"\n{BANNER}\n  {text}\n{BANNER}")


class Verify2ActPipeline:
    def __init__(
        self,
        max_steps: int = 4,               # receding-horizon timesteps (plan -> execute -> re-observe)
        max_replans: int = 2,             # reflect -> re-plan cycles per timestep
        max_requery: int = 2,             # per-horizon world-model re-imaginations / whole-plan re-rolls
        exec_mode: str = "full_plan",     # or "step_by_step"
        theta_c: float = 0.5,
        theta_p: float = 0.6,
        confidence_threshold: float = 0.08,
        simulate_reprompt: bool = False,
        simulate_temporal_inconsistency: bool = False,
        simulate_uncertainty: bool = False,
        execute_unverified: bool = False,
        wm_server: bool = False,          # world model + critic on a remote server (verify2act/remote/v2a_server.py)
        plan_server: bool = False,        # plan + verify on the lab-PC server (research repo: verify2act/robot/server.py)
        dry_run: bool = False,
        jetson_ip: Optional[str] = None,
        bridge_port: int = 9090,
        local: bool = False,
        output_dir: str = "verify2act/assets/rollouts",
    ):
        self.max_steps, self.max_replans, self.max_requery = max_steps, max_replans, max_requery
        self.exec_mode = exec_mode
        self.theta_c, self.theta_p, self.conf = theta_c, theta_p, confidence_threshold
        self.simulate_reprompt = simulate_reprompt
        self.simulate_temporal_inconsistency = simulate_temporal_inconsistency
        self.execute_unverified = execute_unverified
        self.dry_run = dry_run
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.transitions_path: Optional[Path] = None   # set by the session; default <output_dir>/transitions.jsonl
        self.episode_id = "ep_000"
        self.session_name = "run_" + time.strftime("%Y%m%d_%H%M%S")   # plan-server log folder prefix; the session runner overrides it
        self._injected = False

        self.world_model = WorldModelStub(debug_dir=str(self.output_dir))
        self.critic = CriticModel(theta_c, theta_p, force_uncertain=1 if simulate_uncertainty else 0)
        self.planner = VLMPlanner(simulate_reprompt=simulate_reprompt)

        # Robot back-end: remote (roslibpy) / local (rospy) / none (synthetic scene).
        # With dry_run a back-end is used for the camera only; the arm never moves.
        self.robot_client = None
        try:
            if jetson_ip:
                from verify2act.v2a_robot_client import RemoteRobotClient
                self.robot_client = RemoteRobotClient(jetson_ip, bridge_port)
            elif local:
                from verify2act.v2a_robot_client import LocalRobotClient
                self.robot_client = LocalRobotClient()
        except Exception as e:
            if not self.dry_run:
                raise RuntimeError(f"Robot back-end unavailable: {e}") from e
            logger.warning(f"[Pipeline] Robot back-end unavailable ({e}); using synthetic scene.")
        if not self.dry_run and self.robot_client is None:
            raise RuntimeError("Real execution needs --jetson_ip <ip> or --local (or pass --dry_run).")

        self.link = None
        if wm_server:
            ros = getattr(self.robot_client, "_ros", None)
            if ros is None:
                raise RuntimeError("--wm_server needs the rosbridge connection: pass --jetson_ip <ip> (127.0.0.1 on the Jetson).")
            from verify2act.remote.proxies import RemoteCritic, RemoteWorldModel, ServerLink
            self.link = ServerLink(ros)
            self.link.wait_for_server()
            self.world_model, self.critic = RemoteWorldModel(self.link), RemoteCritic(self.link)
            logger.info("[Pipeline] World model + critic are served remotely.")

        self.planner_client = None
        if plan_server:
            ros = getattr(self.robot_client, "_ros", None)
            if ros is None:
                raise RuntimeError("--plan_server needs the rosbridge connection: pass --jetson_ip <ip> (127.0.0.1 on the Jetson).")
            if wm_server:
                raise RuntimeError("--plan_server replaces --wm_server; pass only one.")
            if simulate_reprompt or simulate_temporal_inconsistency or simulate_uncertainty:
                raise RuntimeError("The simulate_* ablations are stub features and are not supported with --plan_server.")
            from verify2act.remote.planner_client import PlanServerClient
            self.planner_client = PlanServerClient(ros)
            self.planner_client.wait_for_server()
            logger.info("[Pipeline] Planning + verification are served by the lab-PC plan server.")

    def close(self):
        if self.link:
            self.link.close()
        if self.planner_client:
            self.planner_client.close()
        if self.robot_client:
            self.robot_client.close()

    # ── observation ───────────────────────────────────────────────────────────

    def observe(self) -> np.ndarray:
        """Live frame from the robot camera, or a synthetic scene when offline."""
        if self.robot_client is not None:
            frame = self.robot_client.capture_frame()
            if frame is not None:
                return frame
            logger.warning("[Pipeline] Camera capture failed; using synthetic scene.")
        return self.world_model.create_synthetic_scene()

    # ── episode ───────────────────────────────────────────────────────────────

    def run(self, language_goal: str) -> bool:
        """One episode. Everything worth logging is left in self.last_result."""
        if self.robot_client is not None and not self.dry_run:
            self.robot_client.execute_subtask(color="red", action="reset", timeout=15.0)   # known pose before observing
        t0 = time.time()
        self._injected = False
        self.planner._proposals = 0
        self.world_model.reset(self.episode_id)   # fresh imagination state for this episode
        self.last_result = {
            "goal": language_goal, "steps": 0, "vlm_calls": 0, "replans": 0, "requeries": 0,
            "temporal_rejections": 0, "goal_rejections": 0, "critic_accepts": 0, "critic_rejects": 0,
            "verified": False, "executed": False, "goal_reached_real": None, "plan": [],
            "executed_actions": [], "reject_reasons": [], "elapsed_s": None,
        }
        try:
            return self._run(language_goal)
        finally:
            self.last_result["elapsed_s"] = round(time.time() - t0, 2)

    def _run(self, goal: str) -> bool:
        if self.planner_client is not None:
            return self._run_plan_server(goal)
        res = self.last_result
        print_banner(f"VERIFY2ACT: GOAL = '{goal}'")
        s_init = self.observe()
        obs, history = s_init, []
        cv2.imwrite(str(self.output_dir / "s_init.jpg"), s_init)

        for t in range(self.max_steps):
            res["steps"] = t + 1
            print_banner(f"TIMESTEP {t + 1} / {self.max_steps}")

            # ── done? judge the REAL observation with the critic's goal head ──
            if t > 0:
                mean, std, why = self.critic.goal_sim_with_uncertainty(obs, goal, s_init)
                done = decide_from_proximity(mean, self.theta_p, std, self.conf).action == "continue"
                res["goal_reached_real"] = done
                print(f"[Real-state goal check] score={mean:.2f} std={std:.2f} -> {'DONE' if done else 'not yet'} ({why})")
                if done:
                    return True

            # ── propose + verify (reflect loop) ──
            plan = self.planner.propose(obs, goal, history)
            res["vlm_calls"] += 1
            if not plan:
                print("[VLM] Empty plan (nothing left to do).")
                break
            accepted, frames = False, []
            for replan in range(self.max_replans + 1):
                self._print_plan(plan, replan)
                accepted, frames, ctx = self._evaluate_plan(plan, obs, goal, s_init)
                if accepted:
                    break
                res["critic_rejects"] += 1
                res["reject_reasons"].append(f"t{t + 1} replan{replan}: {ctx['reason']}")
                self._save_timeline(frames, plan, t + 1, replan, accepted=False)
                if replan < self.max_replans:
                    print(f"--> REFLECT: reprompting VLM with critic feedback (replan {replan + 1}/{self.max_replans})")
                    plan = self.planner.reflect(obs, goal, history, plan, ctx)
                    res["vlm_calls"] += 1
                    res["replans"] += 1
                    if not plan:
                        break
            if accepted:
                res["critic_accepts"] += 1
                res["verified"] = True
                res["plan"] = [st.action_text for st in plan]
                self._save_timeline(frames, plan, t + 1, res["replans"], accepted=True)
            elif not self.execute_unverified:
                logger.error("[Verify2Act] Replan budget exhausted without a verified plan; not executing.")
                return False

            if self.dry_run:
                print("\n[DRY RUN]: verification only, robot not moved.")
                return accepted

            # ── execute ──
            actions = plan[:1] if self.exec_mode == "step_by_step" else plan
            if not self._execute(actions, history, goal_step=t + 1):
                res["goal_reached_real"] = False
                return False
            obs = self.observe()
            cv2.imwrite(str(self.output_dir / f"real_after_step{t + 1}.jpg"), obs)

        # budget spent: final judgement on the real state
        mean, std, _ = self.critic.goal_sim_with_uncertainty(obs, goal, s_init)
        res["goal_reached_real"] = decide_from_proximity(mean, self.theta_p, std, self.conf).action == "continue"
        return bool(res["goal_reached_real"])

    def _run_plan_server(self, goal: str) -> bool:
        """Receding horizon with the plan server: observe -> `plan` (propose + imagine + critics + reflect, remote)
        -> execute -> re-observe, until the server reports `done` or the step budget is spent."""
        from verify2act.remote.planner_client import subtask_from_text
        res = self.last_result
        print_banner(f"VERIFY2ACT (plan server): GOAL = '{goal}'")
        s_init = self.observe()
        cv2.imwrite(str(self.output_dir / "s_init.jpg"), s_init)
        obs, history = s_init, []
        session = f"{self.session_name}_{self.episode_id}"
        self.planner_client.reset(session)

        for t in range(self.max_steps):
            res["steps"] = t + 1
            print_banner(f"TIMESTEP {t + 1} / {self.max_steps}")
            try:
                r = self.planner_client.plan(session, obs, goal, history)
            except (RuntimeError, TimeoutError) as e:
                logger.error(f"[Plan server] {e}")
                res["reject_reasons"].append(f"t{t + 1}: server error: {e}")
                return False
            print(f"[Plan server] planning_call {r.get('planning_call')} took {r.get('elapsed_s')} s "
                  f"(logs on the lab PC: verify2act/output/real/{session}/)")

            st = r["stats"]
            res["vlm_calls"] += st["vlm_calls"]
            res["replans"] += r["replan_attempts"]
            res["requeries"] += st["requeries"]
            res["temporal_rejections"] += st["temporal_rejections"]
            res["goal_rejections"] += st["goal_rejections"]
            res["critic_rejects"] += sum(not e["accepted"] for e in r["evaluations"])
            for i, e in enumerate(r["evaluations"]):
                print(f"  [eval {i + 1}] {e['plan']}  tc={e['tc']}  goal={e['goal']}  accepted={e['accepted']}")
            for a in r["reflection_analyses"]:
                print(f"  [reflect] {a}")

            if r["done"]:
                print("[Plan server] Goal judged complete (VLM 'done', confirmed by the goal head).")
                res["goal_reached_real"] = True
                return True
            if r["invalid_steps"] or not r["plan"]:
                logger.error(f"[Plan server] Unusable plan {r['plan']} (outside the vocabulary: {r['invalid_steps']}); not executing.")
                res["reject_reasons"].append(f"t{t + 1}: unusable plan {r['plan']}")
                return False
            if r["accepted"]:
                res["critic_accepts"] += 1
                res["verified"] = True
            else:
                res["reject_reasons"].append(f"t{t + 1}: not verified after {r['replan_attempts']} replans "
                                             f"(failed_step={r.get('failed_step')})")
                if not self.execute_unverified:
                    logger.error("[Verify2Act] Replan budget exhausted without a verified plan; not executing.")
                    return False

            try:
                plan = [subtask_from_text(s) for s in r["plan"]]
            except ValueError as e:
                logger.error(f"[Plan server] {e}; not executing.")
                res["reject_reasons"].append(f"t{t + 1}: {e}")
                return False
            res["plan"] = list(r["plan"])
            self._print_plan(plan, r["replan_attempts"])
            if self.dry_run:
                print("\n[DRY RUN]: verification only, robot not moved.")
                return bool(r["accepted"])

            actions = plan[:1] if self.exec_mode == "step_by_step" else plan
            if not self._execute(actions, history, goal_step=t + 1):
                res["goal_reached_real"] = False
                return False
            obs = self.observe()
            cv2.imwrite(str(self.output_dir / f"real_after_step{t + 1}.jpg"), obs)

        return False   # step budget spent without `done`; the human y/n label decides real success

    # ── imagination + critic ──────────────────────────────────────────────────

    def _evaluate_plan(self, plan: List[Subtask], obs: np.ndarray, goal: str, s_init: np.ndarray):
        """Verify one plan. Local stubs run the loop here; with --wm_server the server runs it (one round trip)."""
        res = self.last_result
        actions = [st.action_text for st in plan]
        if self.link is not None:
            from verify2act.remote.proxies import evaluate_plan_remote
            r = evaluate_plan_remote(self.link, self.episode_id, actions, obs, goal, s_init, self.theta_c,
                                     self.theta_p, self.conf, self.max_requery,
                                     inject_fault=self.simulate_temporal_inconsistency and not self._injected)
            self._injected = self._injected or self.simulate_temporal_inconsistency
            for st in r["steps"]:
                print(f"  [Temporal H{st['horizon']}] score={st['mean']:.2f} std={st['std']:.2f} -> {st['decision'].upper()}  ({st['reason']})")
            if r["goal"]:
                g = r["goal"]
                print(f"  [Goal head] score={g['mean']:.2f} std={g['std']:.2f} -> {g['decision'].upper()}  ({g['reason']})")
        else:
            def inject():
                fire = self.simulate_temporal_inconsistency and not self._injected
                self._injected = self._injected or fire
                return fire
            r = evaluate_plan(self.world_model, self.critic, actions, obs, goal, s_init, self.theta_c, self.theta_p,
                              self.conf, self.max_requery, inject_fault=inject)
        for k in ("requeries", "temporal_rejections", "goal_rejections"):
            res[k] += r[k]
        return r["accepted"], r["frames"], r["ctx"]

    # ── execution ─────────────────────────────────────────────────────────────

    def _execute(self, actions: List[Subtask], history: List[str], goal_step: int) -> bool:
        print_banner("EXECUTING VERIFIED PLAN ON PHYSICAL ROBOT")
        for i, st in enumerate(actions):
            print(f"\n[Executing {i + 1}/{len(actions)}]: {st.action_text}")
            before = self.observe()
            ok = self._run_skill(st)
            time.sleep(2.0)   # let the arm and camera settle
            after = self.observe()
            self._log_transition(goal_step, st.action_text, before, after, ok)
            if not ok:
                logger.error(f"Robot failed executing: {st.action_text}")
                return False
            history.append(st.action_text)
            self.last_result["executed_actions"].append(st.action_text)
            self.last_result["executed"] = True
        return True

    def _run_skill(self, st: Subtask) -> bool:
        """One subtask = one complete pick-and-place, ending with nothing held. stack / rearrange chain the grasp
        node's locate -> pick -> place_on | place_at back to back: the arm never holds a block while waiting."""
        rc = self.robot_client
        if st.kind == "pick_place":
            return rc.execute_subtask(color=st.color, target=st.target_placement, timeout=60.0, action="pick_place")
        # Locate the base / reference block from the unobstructed observation pose, before anything is held.
        if not rc.execute_subtask(color=st.base_color, action="locate", timeout=20.0):
            logger.error(f"Could not locate the {st.base_color} block; aborting before the pick.")
            return False
        if not rc.execute_subtask(color=st.color, target="hold", timeout=60.0, action="pick"):
            return False
        return rc.execute_subtask(color=st.color, target=st.target_placement, timeout=60.0,
                                  action="place_on" if st.kind == "stack" else "place_at", base_color=st.base_color)

    def _log_transition(self, step: int, action_text: str, before: np.ndarray, after: np.ndarray, ok: bool):
        """Real-robot transition in the research repo's transitions.jsonl schema (train the WM / critic on it)."""
        d = self.output_dir / "transitions"
        d.mkdir(exist_ok=True)
        n = len(list(d.glob("*_t.jpg")))
        p0, p1 = d / f"{n:03d}_t.jpg", d / f"{n:03d}_t1.jpg"
        cv2.imwrite(str(p0), before)
        cv2.imwrite(str(p1), after)
        path = self.transitions_path or (self.output_dir / "transitions.jsonl")
        with open(path, "a") as f:
            f.write(json.dumps({"episode_id": self.episode_id, "timestep": step, "action_text": action_text,
                                "image_t": str(p0), "image_t1": str(p1), "skill_ok": bool(ok),
                                "timestamp": time.time()}) + "\n")

    # ── display / figures ─────────────────────────────────────────────────────

    def _print_plan(self, plan: List[Subtask], replan: int):
        print(f"\n[VLM plan{' (revised %d)' % replan if replan else ''}: {len(plan)} horizons]")
        for i, st in enumerate(plan):
            print(f"  Horizon {i + 1}: '{st.action_text}'")

    def _save_timeline(self, frames, plan, step: int, replan: int, accepted: bool):
        """Montage of S_0 .. S_H (imagined) for the figure; one image per evaluated plan."""
        try:
            tag = "accepted" if accepted else "rejected"
            thumbs = []
            for idx, frame in enumerate(frames):
                th = cv2.resize(frame, (320, 240))
                label = "S0: observed" if idx == 0 else f"S{idx}: {plan[idx - 1].action_text[:34]}"
                cv2.rectangle(th, (0, 0), (320, 24), (20, 20, 20), -1)
                cv2.putText(th, label, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1)
                thumbs.append(th)
            path = self.output_dir / f"t{step}_replan{replan}_{tag}_timeline.jpg"
            cv2.imwrite(str(path), np.hstack(thumbs))
        except Exception as e:
            logger.warning(f"[Rollout] Could not save timeline montage: {e}")


def main():
    ap = argparse.ArgumentParser(description="Verify2Act pipeline on DOFBOT Pro (single episode)")
    ap.add_argument("--task", default="task1a", help="preset: %s" % ", ".join(TASK_PRESETS))
    ap.add_argument("--goal", default="", help="custom language goal (overrides --task)")
    ap.add_argument("--dry_run", action="store_true", help="verify only; the arm never moves")
    ap.add_argument("--jetson_ip", default=None, help="Jetson running rosbridge (camera + execution)")
    ap.add_argument("--bridge_port", type=int, default=9090)
    ap.add_argument("--local", action="store_true", help="run on the Jetson itself via rospy")
    add_loop_args(ap)
    args = ap.parse_args()
    goal = args.goal or TASK_PRESETS.get(args.task.lower(), args.task)
    pipeline = Verify2ActPipeline(dry_run=args.dry_run, jetson_ip=args.jetson_ip, bridge_port=args.bridge_port,
                                  local=args.local, **loop_kwargs(args))
    try:
        ok = pipeline.run(goal)
    finally:
        pipeline.close()
    sys.exit(0 if ok else 1)


def add_loop_args(ap):
    """CLI flags shared with v2a_session.py."""
    ap.add_argument("--max_steps", type=int, default=4, help="receding-horizon timesteps")
    ap.add_argument("--max_replans", type=int, default=2, help="reflect/re-plan budget per timestep")
    ap.add_argument("--max_requery", type=int, default=2)
    ap.add_argument("--exec_mode", choices=["full_plan", "step_by_step"], default="full_plan")
    ap.add_argument("--theta_c", type=float, default=0.5, help="temporal-consistency threshold")
    ap.add_argument("--theta_p", type=float, default=0.6, help="goal-proximity threshold")
    ap.add_argument("--simulate_reprompt", action="store_true", help="first VLM proposal is deliberately flawed")
    ap.add_argument("--simulate_temporal_inconsistency", action="store_true", help="first imagined transition is wrong")
    ap.add_argument("--simulate_uncertainty", action="store_true", help="critic is uncertain once (exercises requery)")
    ap.add_argument("--wm_server", action="store_true", help="use the remote world-model/critic server (needs --jetson_ip)")
    ap.add_argument("--plan_server", action="store_true",
                    help="plan + verify on the lab-PC Verify2Act server (verify2act/robot/server.py); needs --jetson_ip")
    ap.add_argument("--execute_unverified", action="store_true", help="run the last plan even if never verified (unsafe)")


def loop_kwargs(args) -> dict:
    keys = ["max_steps", "max_replans", "max_requery", "exec_mode", "theta_c", "theta_p", "simulate_reprompt",
            "simulate_temporal_inconsistency", "simulate_uncertainty", "execute_unverified", "wm_server", "plan_server"]
    return {k: getattr(args, k) for k in keys}


if __name__ == "__main__":
    main()
