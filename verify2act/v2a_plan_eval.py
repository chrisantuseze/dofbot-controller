"""
verify2act/v2a_plan_eval.py
===========================
Imagine + critic evaluation of ONE candidate plan, following the research repo's
BeamSearchPlanner._evaluate_trajectory:

    per horizon  : world model imagines S_{t+1}; temporal head -> continue | requery (re-imagine, rewinding state)
    after last   : goal head on the final imagined state -> continue (accept) | requery (re-roll plan) | reflect

`wm` needs  imagine(frame, action_text, simulate_inconsistency=False) -> obj with .imagined_frame
`critic` needs  temporal_sim_with_uncertainty(cur, nxt, action) and goal_sim_with_uncertainty(frame, goal, init, executed)
Both are the local stubs or the remote proxies, so this runs on the Jetson or inside the stub server.
"""

from typing import Callable, List, Optional

import numpy as np

from verify2act.v2a_decisions import check_rollout_consistency, decide_from_proximity


def evaluate_plan(wm, critic, actions: List[str], obs: np.ndarray, goal: str, s_init: Optional[np.ndarray],
                  theta_c: float = 0.5, theta_p: float = 0.6, confidence: float = 0.08, max_requery: int = 2,
                  inject_fault: Callable[[], bool] = lambda: False, log: Callable[[str], None] = print) -> dict:
    out = {"accepted": False, "frames": [obs], "steps": [], "goal": None, "requeries": 0,
           "temporal_rejections": 0, "goal_rejections": 0,
           "ctx": {"reason": "", "failed_step": None, "temporal_scores": [], "proximity": None}}
    why = ""
    for roll in range(max_requery + 1):                    # goal-head 'requery' re-rolls the whole plan
        frames, s_cur, t_scores, steps = [obs], obs, [], []
        for h, act in enumerate(actions):
            for retry in range(max_requery + 1):           # temporal 'requery' re-imagines this horizon
                rollout = wm.imagine(s_cur, act, simulate_inconsistency=bool(inject_fault()))
                mean, std, why = critic.temporal_sim_with_uncertainty(s_cur, rollout.imagined_frame, act)
                dec = check_rollout_consistency(mean, theta_c, std, confidence)
                steps.append({"horizon": h + 1, "action": act, "mean": float(mean), "std": float(std),
                              "decision": dec.action, "reason": why})
                log(f"  [Temporal H{h + 1}] score={mean:.2f} std={std:.2f} -> {dec.action.upper()}  ({dec.reason}; {why})")
                if dec.action == "continue":
                    break
                out["requeries"] += 1
                out["temporal_rejections"] += 1
                log(f"    world model re-imagining horizon {h + 1} (attempt {retry + 2}/{max_requery + 1})")
            else:
                out.update(frames=frames, steps=steps)
                out["ctx"] = {"reason": f"horizon {h + 1} ('{act}') kept failing temporal consistency: {why}",
                              "failed_step": h, "temporal_scores": t_scores, "proximity": None}
                return out
            t_scores.append(float(mean))
            s_cur = rollout.imagined_frame
            frames.append(s_cur)

        mean, std, why = critic.goal_sim_with_uncertainty(s_cur, goal, s_init, actions)
        dec = decide_from_proximity(mean, theta_p, std, confidence)
        log(f"  [Goal head] score={mean:.2f} std={std:.2f} -> {dec.action.upper()}  ({dec.reason}; {why})")
        out.update(frames=frames, steps=steps, goal={"mean": float(mean), "std": float(std), "decision": dec.action, "reason": why})
        if dec.action == "continue":
            out["accepted"] = True
            out["ctx"] = {}
            return out
        if dec.action == "requery":
            out["requeries"] += 1
            log(f"    critic uncertain about the goal estimate; re-rolling the plan ({roll + 1}/{max_requery})")
            continue
        out["goal_rejections"] += 1
        out["ctx"] = {"reason": why, "failed_step": None, "temporal_scores": t_scores, "proximity": float(mean)}
        return out
    out["ctx"] = {"reason": "goal estimate stayed uncertain after re-rolls", "failed_step": None,
                  "temporal_scores": [], "proximity": None}
    return out
