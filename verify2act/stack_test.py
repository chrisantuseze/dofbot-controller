#!/usr/bin/env python3
"""
Direct stacking test, no VLM / critic / world model:
    reset (home, once) -> locate BASE block (cached) -> pick TOP block, lift -> place TOP on BASE -> home.

    python3 verify2act/stack_test.py --top green --base red                  # one run
    python3 verify2act/stack_test.py --top green --base red --trials 10      # N runs at different positions:
        before each run: rearrange the blocks, press Enter; after it: answer y/n (+ optional note).
Each run is appended to verify2act/results/stack_test/<session>/trials.jsonl with the block world poses
(from the detector), so misses can be related to position. summary.md is rewritten after every run.
Live tuning (no restart):  rosparam set /lang_color_grasp/{stack_dz,stack_dx,stack_dy,lift_j2_deg} <value>

Rearrangement (place_at) instead of stacking: put TOP on the table beside BASE.
    python3 verify2act/stack_test.py --top red --base blue --relation left_of --trials 5
    Live tuning:  rosparam set /lang_color_grasp/{place_gap,place_dz} <value>
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from verify2act.v2a_robot_client import RemoteRobotClient   # noqa: E402


def run_once(c, a, out):
    def snap(tag):
        f = c.capture_frame()
        if f is not None:
            cv2.imwrite(str(out / f"{tag}.jpg"), f)

    steps = [
        ("reset", dict(color=a.top, action="reset", timeout=20.0)),
        ("locate_base", dict(color=a.base, action="locate", timeout=20.0)),
        ("pick_top", dict(color=a.top, action="pick", timeout=60.0)),
        ("place_on_base", dict(color=a.top, action="place_on", base_color=a.base, timeout=60.0)) if not a.relation else
        ("place_at_base", dict(color=a.top, action="place_at", base_color=a.base, target=a.relation, timeout=60.0)),
    ]
    rec = {"top": a.top, "base": a.base, "start": time.time()}
    for name, kw in steps:
        print(f"[stack_test] {name} ...", flush=True)
        ok = c.execute_subtask(**kw)
        if name == "reset":
            snap("0_before")
        if name in ("locate_base", "pick_top"):
            rec[f"{a.base if name == 'locate_base' else a.top}_pose"] = c._result.get("pose")
        if not ok:
            print(f"[stack_test] {name}: FAILED", flush=True)
            rec["failed_step"] = name
            return rec
        print(f"[stack_test] {name}: ok", flush=True)
        time.sleep(1.0)
        if name == "pick_top":
            snap("0b_holding")   # eye-in-hand camera: is the block in the gripper?
    snap("1_after")
    # Measure the placement: locate the TOP block where it ended up (arm is back at the observation pose) and
    # compare with the base pose cached before the pick. Meaningful when it stayed on; if it fell, it's where it fell.
    if c.execute_subtask(color=a.top, action="locate", timeout=30.0):
        after = c._result.get("pose")
        base = rec.get(f"{a.base}_pose")
        rec[f"{a.top}_after_pose"] = after
        if after and base:
            rec["place_err"] = [after[0] - base[0], after[1] - base[1]]
            print(f"[stack_test] placement error (top - base): dx={rec['place_err'][0]*100:+.1f} cm, "
                  f"dy={rec['place_err'][1]*100:+.1f} cm", flush=True)
    return rec


def write_summary(session, rows):
    labeled = [r for r in rows if r.get("stacked") is not None]
    ok = sum(1 for r in labeled if r["stacked"])
    lines = [f"# Stack test {session.name}", "",
             f"Stacked: {ok}/{len(labeled)} labeled runs ({len(rows)} total)", "",
             "| run | base (x, y) m | top (x, y) m | base r m | place err (dx, dy) cm | stacked | note |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        b = r.get(f"{r['base']}_pose") or [float('nan')] * 3
        t = r.get(f"{r['top']}_pose") or [float('nan')] * 3
        lines.append(f"| {r['run']} | ({b[0]:.3f}, {b[1]:.3f}) | ({t[0]:.3f}, {t[1]:.3f}) | {math.hypot(b[0], b[1]):.3f} | "
                     f"{'(%+.1f, %+.1f)' % (r['place_err'][0] * 100, r['place_err'][1] * 100) if r.get('place_err') else '-'} | "
                     f"{ {True: 'yes', False: 'no', None: '-'}[r.get('stacked')] }{' (' + r['failed_step'] + ' failed)' if r.get('failed_step') else ''} | {r.get('note', '')} |")
    (session / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:3]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", default="green")
    ap.add_argument("--base", default="red")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--relation", choices=["left_of", "right_of"], default=None,
                    help="rearrangement: place TOP on the table beside BASE instead of on it")
    ap.add_argument("--jetson_ip", default="127.0.0.1")
    a = ap.parse_args()
    interactive = sys.stdin.isatty()

    session = Path(__file__).resolve().parent / "results" / "stack_test" / time.strftime("%Y%m%d_%H%M%S")
    session.mkdir(parents=True, exist_ok=True)
    c = RemoteRobotClient(a.jetson_ip)
    rows = []
    try:
        for i in range(1, a.trials + 1):
            if interactive and a.trials > 1:
                input(f"\n=== run {i}/{a.trials}: place the {a.top} and {a.base} blocks, then press Enter ===")
            out = session / f"run_{i:02d}"
            out.mkdir(exist_ok=True)
            rec = run_once(c, a, out)
            rec["run"] = i
            rec["stacked"] = None
            if interactive:
                where = f"end up {a.relation.replace('_', ' ')} the" if a.relation else "stay on the"
                ans = input(f"[run {i}] did the {a.top} block {where} {a.base} block? [y/n]: ").strip().lower()
                rec["stacked"] = ans.startswith("y") if ans else None
                rec["note"] = input("  note (e.g. 'landed 1cm left', Enter to skip): ").strip()
            rows.append(rec)
            with open(session / "trials.jsonl", "a") as f:
                f.write(json.dumps(rec) + "\n")
            write_summary(session, rows)
        print(f"[stack_test] done. Results in {session}")
    finally:
        c.close()


if __name__ == "__main__":
    main()
