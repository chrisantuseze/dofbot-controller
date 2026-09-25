#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify2act/v2a_session.py
=========================
One session = ONE task run for N episodes.

    python3 verify2act/v2a_session.py --task task1a --episodes 10 --jetson_ip 127.0.0.1

For every episode it:
  1. asks you to reset the scene and press Enter   (type q + Enter to stop early)
  2. runs the full Verify2Act loop (plan -> imagine -> critics -> execute)
  3. asks whether the episode really succeeded (y/n) and an optional note
  4. appends the result to episodes.jsonl and rewrites summary.md / summary.json
At the end it prints the analysis of all episodes.

Output folder: verify2act/results/<task>_<timestamp>/
    episodes.jsonl   one line per episode, written immediately (crash-safe)
    ep_NNN/          imagined timelines + real final frame of each episode
    transitions.jsonl real-robot (image_t, action_text, image_t1) transitions for training the WM / critic
    summary.md/json  success, critic precision, steps, replans, VLM calls, timing
"""

import argparse
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from verify2act.v2a_pipeline import TASK_PRESETS, Verify2ActPipeline, add_loop_args, loop_kwargs


def _rate(num: int, den: int) -> Optional[float]:
    return round(num / den, 3) if den else None


def summarize(episodes: List[dict]) -> dict:
    n = len(episodes)
    verified = [e for e in episodes if e["verified"]]
    executed = [e for e in episodes if e["executed"]]
    labeled = [e for e in executed if e.get("real_success") is not None]
    real_ok = [e for e in labeled if e["real_success"]]
    per_task = {}
    for e in episodes:
        t = per_task.setdefault(e["task"], {"episodes": 0, "verified": 0, "real_success": 0, "labeled": 0})
        t["episodes"] += 1
        t["verified"] += e["verified"]
        if e.get("real_success") is not None:
            t["labeled"] += 1
            t["real_success"] += bool(e["real_success"])
    tp = sum(1 for e in labeled if e["real_success"])
    avg = lambda k: round(statistics.mean(e[k] for e in episodes), 2) if episodes else None
    return {
        "episodes": n,
        "real_success_rate": _rate(len(real_ok), len(labeled)),           # human-labeled, executed episodes
        "real_success_overall": _rate(len(real_ok), n) if labeled else None,
        "verified_rate": _rate(len(verified), n),                         # critic accepted a plan within the replan budget
        "accepted_without_reflect": _rate(sum(1 for e in verified if e["replans"] == 0), n),
        "critic_precision": _rate(tp, len(labeled)),                      # accepted+executed plans that really succeeded
        "false_accepts": len(labeled) - tp,                               # accepted+executed but really failed
        "avg_timesteps": avg("steps"),
        "avg_replans": avg("replans"),
        "avg_vlm_calls": avg("vlm_calls"),
        "total_requeries": sum(e["requeries"] for e in episodes),
        "total_temporal_rejections": sum(e["temporal_rejections"] for e in episodes),
        "total_goal_rejections": sum(e["goal_rejections"] for e in episodes),
        "mean_episode_time_s": avg("elapsed_s"),
        "per_task": per_task,
    }


def write_summary(out_dir: Path, episodes: List[dict], meta: dict):
    s = summarize(episodes)
    (out_dir / "summary.json").write_text(json.dumps({"meta": meta, "summary": s}, indent=2))
    lines = [f"# Verify2Act session {meta['session']}", "",
             f"- backend: `{meta['backend']}`  exec_mode: {meta['exec_mode']}  max_replans: {meta['max_replans']}  theta_c/theta_p: {meta['theta_c']}/{meta['theta_p']}  dry_run: {meta['dry_run']}", "",
             "| metric | value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in s.items() if k != "per_task"]
    lines += ["", "| task | episodes | verified | real success / labeled |", "|---|---|---|---|"]
    lines += [f"| {k} | {v['episodes']} | {v['verified']} | {v['real_success']}/{v['labeled']} |" for k, v in s["per_task"].items()]
    lines += ["", "| # | task | steps | replans | vlm calls | verified | executed | real | time (s) |", "|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {e['episode']} | {e['task']} | {e['steps']} | {e['replans']} | {e['vlm_calls']} | {e['verified']} | {e['executed']} | "
              f"{e.get('real_success')} | {e['elapsed_s']} |" for e in episodes]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n")
    return s


def _ask_outcome() -> tuple:
    """Return (real_success or None, note). Ctrl-C/EOF leaves it unlabeled."""
    try:
        while True:
            a = input("Real outcome of this episode? [y]=success  [n]=failure  [s]=skip label > ").strip().lower()
            if a in ("y", "n", "s"):
                break
        note = input("Note (optional, e.g. 'collided with bin') > ").strip() if a != "s" else ""
        return (None if a == "s" else a == "y"), note
    except (EOFError, KeyboardInterrupt):
        return None, ""


def main():
    ap = argparse.ArgumentParser(description="Verify2Act session: one task, N episodes",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--jetson_ip", default=None)
    ap.add_argument("--bridge_port", type=int, default=9090)
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--dry_run", action="store_true", help="verify only; the arm never moves")
    add_loop_args(ap)
    ap.add_argument("--task", required=True, help="preset (%s) or a quoted free-text goal" % ", ".join(TASK_PRESETS))
    ap.add_argument("--episodes", type=int, default=10, help="number of episodes to run")
    ap.add_argument("--no_confirm", action="store_true", help="do not ask for the real outcome")
    ap.add_argument("--session_name", default=None)
    ap.add_argument("--results_root", default=str(_ROOT / "verify2act" / "results"))
    args = ap.parse_args()

    task, goal = (args.task, TASK_PRESETS[args.task.lower()]) if args.task.lower() in TASK_PRESETS else ("custom", args.task)
    name = args.session_name or f"{task}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir = Path(args.results_root) / name
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {"session": name, "task": task, "goal": goal, "episodes_planned": args.episodes, "backend": args.jetson_ip or ("local" if args.local else "synthetic"),
            "dry_run": args.dry_run, **loop_kwargs(args),
            "started": datetime.now().isoformat(timespec="seconds")}
    if args.plan_server:
        # the lab-PC server decides these; the Jetson's --theta_*/--max_* flags are ignored
        from verify2act.remote.planner_client import SERVER_SETTINGS
        meta.update(SERVER_SETTINGS, backend=f"{meta['backend']}+plan_server")

    pipe = Verify2ActPipeline(
        **loop_kwargs(args), dry_run=args.dry_run, jetson_ip=args.jetson_ip, bridge_port=args.bridge_port,
        local=args.local, output_dir=str(out_dir),
    )
    pipe.session_name = name   # plan-server log folders: <name>_ep_NNN

    episodes: List[dict] = []
    print(f"\nSession '{name}'\nTask   : {task}\nGoal   : {goal}\nEpisodes: {args.episodes}\nResults -> {out_dir}\n")

    try:
        for idx in range(1, args.episodes + 1):
            if input(f"\n--- Episode {idx}/{args.episodes} --- Reset the scene, then press Enter (q = stop) ... ").strip().lower() in ("q", "quit"):
                break
            ep_dir = out_dir / f"ep_{idx:03d}"
            ep_dir.mkdir(exist_ok=True)
            pipe.output_dir = ep_dir
            pipe.episode_id = f"ep_{idx:03d}"
            pipe.transitions_path = out_dir / "transitions.jsonl"

            ok = pipe.run(goal)
            rec = {"episode": idx, "task": task, **pipe.last_result, "run_ok": bool(ok),
                   "real_success": None, "note": "", "timestamp": time.time()}
            if rec["executed"] and not args.no_confirm:
                rec["real_success"], rec["note"] = _ask_outcome()
            elif not rec["verified"]:
                rec["real_success"] = False   # critic never accepted a plan: nothing was executed
            episodes.append(rec)
            with open(out_dir / "episodes.jsonl", "a") as f:
                f.write(json.dumps(rec) + "\n")
            write_summary(out_dir, episodes, meta)
    except (KeyboardInterrupt, EOFError):
        print("\nInterrupted.")
    finally:
        pipe.close()
        meta["ended"] = datetime.now().isoformat(timespec="seconds")
        s = write_summary(out_dir, episodes, meta)
        print(f"\n=== Session summary ({len(episodes)} episodes) ===")
        print(json.dumps({k: v for k, v in s.items() if k != "per_task"}, indent=2))
        print(f"Saved: {out_dir}/summary.md, summary.json, episodes.jsonl")


if __name__ == "__main__":
    main()
