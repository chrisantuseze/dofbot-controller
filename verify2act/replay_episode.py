#!/usr/bin/env python3
"""
verify2act/replay_episode.py
============================
Renders a recorded Dofbot Pro HDF5 episode to an annotated .mp4 video.
No robot or ROS connection required — runs entirely offline.

Reads:
    observation/images/top  (T, H, W, 3)  uint8 RGB
    observation/state       (T, 6)         float32 joint rad
    action                  (T, 6)         float32 joint rad
    attrs: fps, task, episode_index, num_frames

Output:
    <episode_stem>.mp4  — written alongside the .hdf5 file by default.

Usage
-----
    # Single episode
    python3 verify2act/replay_episode.py \\
        dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000019.hdf5

    # With joint-state overlay, custom fps
    python3 verify2act/replay_episode.py episode_000019.hdf5 --show_joints --fps 15

    # Batch — render every episode in a dataset directory
    python3 verify2act/replay_episode.py \\
        dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/ --all

    # Custom output location
    python3 verify2act/replay_episode.py episode_000019.hdf5 --output_dir /tmp/videos
"""

import argparse
import math
import sys
from pathlib import Path

import cv2
import h5py
import numpy as np

# ── Joint metadata ────────────────────────────────────────────────────────────
JOINT_NAMES  = ["Base", "Shoulder", "Elbow", "Wrist-P", "Wrist-T", "Gripper"]
NUM_JOINTS   = 6
RAD2DEG      = 180.0 / math.pi

# ── Visual style ──────────────────────────────────────────────────────────────
FONT            = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_SM   = 0.45
FONT_SCALE_MD   = 0.60
FONT_SCALE_LG   = 0.75
FONT_THICK      = 1
FONT_THICK_BOLD = 2

BG_COLOR        = (20,  20,  20)
ACCENT_GREEN    = (80,  200, 100)
TEXT_PRIMARY    = (240, 240, 240)
TEXT_SECONDARY  = (160, 160, 160)
BORDER_COLOR    = (60,  60,  60)

BAR_HEIGHT      = 8
BAR_MAX_WIDTH   = 180

JOINT_SAFE_MIN = [  0.0,  30.0,   0.0,   0.0,   0.0,  30.0]
JOINT_SAFE_MAX = [180.0, 270.0, 180.0, 270.0, 180.0, 180.0]


# ── Conversion: stored radians → servo degrees ────────────────────────────────

def action_rad_to_deg(joints_rad: np.ndarray) -> np.ndarray:
    """
    Reverse the data_collector.py radians encoding back to servo degrees.

    data_collector stores:
      joints 0-4:  rad = (servo_deg - 90) * pi/180
      joint  5:    grip_state_deg = interp(servo_deg, [30,180]->[0,90])
                   rad = (grip_state_deg - 90) * pi/180
    """
    deg = joints_rad * RAD2DEG + 90.0  # joints 0-4 (and raw gripper)
    grip_state_deg = float(joints_rad[5]) * RAD2DEG + 90.0
    deg[5] = float(np.interp(grip_state_deg, [0.0, 90.0], [30.0, 180.0]))
    return deg


# ── Annotation helpers ────────────────────────────────────────────────────────

def _put_text_with_bg(frame: np.ndarray, text: str, org: tuple,
                      font_scale: float = FONT_SCALE_MD,
                      font_thick: int = FONT_THICK,
                      text_color: tuple = TEXT_PRIMARY,
                      bg_color: tuple = BG_COLOR,
                      padding: int = 4) -> None:
    """Draw text with a filled background rectangle for readability."""
    (tw, th), baseline = cv2.getTextSize(text, FONT, font_scale, font_thick)
    x, y = org
    cv2.rectangle(frame,
                  (x - padding, y - th - padding),
                  (x + tw + padding, y + baseline + padding),
                  bg_color, -1)
    cv2.putText(frame, text, (x, y), FONT, font_scale, text_color, font_thick,
                cv2.LINE_AA)


def _draw_joint_bars(frame: np.ndarray, joints_deg: np.ndarray,
                     origin_x: int, origin_y: int) -> None:
    """Horizontal bar per joint showing position within safe range."""
    label_w = 72
    gap     = 4

    for i, (name, val, lo, hi) in enumerate(
            zip(JOINT_NAMES, joints_deg, JOINT_SAFE_MIN, JOINT_SAFE_MAX)):
        y     = origin_y + i * (BAR_HEIGHT + gap)
        bar_x = origin_x + label_w
        bar_w = BAR_MAX_WIDTH
        frac  = float(np.clip((val - lo) / max(hi - lo, 1.0), 0.0, 1.0))
        fill  = int(frac * bar_w)

        cv2.putText(frame, f"{name}:", (origin_x, y + BAR_HEIGHT - 1),
                    FONT, 0.35, TEXT_SECONDARY, 1, cv2.LINE_AA)
        cv2.rectangle(frame, (bar_x, y), (bar_x + bar_w, y + BAR_HEIGHT),
                      BORDER_COLOR, -1)
        cv2.rectangle(frame, (bar_x, y), (bar_x + fill, y + BAR_HEIGHT),
                      ACCENT_GREEN, -1)
        cv2.putText(frame, f"{val:6.1f}deg",
                    (bar_x + bar_w + 4, y + BAR_HEIGHT - 1),
                    FONT, 0.35, TEXT_SECONDARY, 1, cv2.LINE_AA)


def annotate_frame(frame_rgb: np.ndarray,
                   step: int,
                   total: int,
                   task: str,
                   joints_deg: np.ndarray,
                   show_joints: bool) -> np.ndarray:
    """Return an annotated BGR copy of an RGB frame."""
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    h, w = frame_bgr.shape[:2]

    # Top bar: task label
    task_display = task if len(task) <= 60 else task[:57] + "..."
    _put_text_with_bg(frame_bgr, task_display, (8, 20),
                      font_scale=FONT_SCALE_MD,
                      font_thick=FONT_THICK_BOLD,
                      text_color=ACCENT_GREEN)

    # Top-right: step counter
    step_text = f"step {step + 1:04d} / {total:04d}"
    (tw, _), _ = cv2.getTextSize(step_text, FONT, FONT_SCALE_SM, FONT_THICK)
    _put_text_with_bg(frame_bgr, step_text, (w - tw - 14, 20),
                      font_scale=FONT_SCALE_SM,
                      text_color=TEXT_SECONDARY)

    # Bottom: progress bar
    bar_y   = h - 6
    bar_end = int((step / max(total - 1, 1)) * w)
    cv2.rectangle(frame_bgr, (0, bar_y), (w, h), BG_COLOR, -1)
    cv2.rectangle(frame_bgr, (0, bar_y), (bar_end, h), ACCENT_GREEN, -1)

    # Joint bars (optional)
    if show_joints:
        panel_h = NUM_JOINTS * (BAR_HEIGHT + 4) + 12
        panel_y = h - 14 - panel_h
        cv2.rectangle(frame_bgr,
                      (0, panel_y - 4),
                      (4 + 72 + BAR_MAX_WIDTH + 60, h - 10),
                      (10, 10, 10), -1)
        _draw_joint_bars(frame_bgr, joints_deg, origin_x=4, origin_y=panel_y)

    return frame_bgr


# ── Core render function ──────────────────────────────────────────────────────

def render_episode(hdf5_path: Path,
                   output_dir: "Path | None",
                   fps_override: "float | None",
                   show_joints: bool) -> Path:
    """Render one episode HDF5 to .mp4. Returns the output path."""
    with h5py.File(hdf5_path, "r") as f:
        fps           = float(fps_override or f.attrs.get("fps", 10))
        episode_index = int(f.attrs.get("episode_index", 0))
        task_raw      = f.attrs.get("task", "")
        task          = task_raw.decode() if isinstance(task_raw, bytes) else str(task_raw)

        images  = f["observation/images/top"][()]   # (T, H, W, 3) uint8
        actions = f["action"][()]                   # (T, 6) float32 rad

    T, H, W, _ = images.shape
    print(f"  Episode {episode_index:06d} | {T} frames @ {fps:.1f} fps | {W}x{H}")
    print(f"  Task: {task or '(no task label)'}")

    out_dir = output_dir if output_dir else hdf5_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (hdf5_path.stem + ".mp4")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (W, H))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open VideoWriter for {out_path}")

    for t in range(T):
        joints_deg = action_rad_to_deg(actions[t].copy())
        frame_bgr  = annotate_frame(images[t], t, T, task, joints_deg, show_joints)
        writer.write(frame_bgr)

    writer.release()
    print(f"  -> {out_path}")
    return out_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Render a Dofbot Pro HDF5 episode to an annotated .mp4 video.")
    parser.add_argument("input",
                        help="Path to a .hdf5 file or a dataset directory (with --all).")
    parser.add_argument("--all", action="store_true",
                        help="Render every episode_*.hdf5 in the given directory.")
    parser.add_argument("--output_dir", default=None,
                        help="Where to write .mp4 files. Defaults to alongside the .hdf5.")
    parser.add_argument("--fps", type=float, default=None,
                        help="Override the fps stored in the episode attrs.")
    parser.add_argument("--show_joints", action="store_true",
                        help="Overlay a joint-state bar chart on each frame.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir) if args.output_dir else None

    if args.all:
        if not input_path.is_dir():
            print(f"ERROR: --all requires a directory, got: {input_path}", file=sys.stderr)
            sys.exit(1)
        episodes = sorted(input_path.glob("episode_*.hdf5"))
        if not episodes:
            print(f"No episode_*.hdf5 files found in {input_path}", file=sys.stderr)
            sys.exit(1)
        print(f"Rendering {len(episodes)} episode(s) from {input_path}\n")
        for ep in episodes:
            print(f"[{ep.name}]")
            render_episode(ep, output_dir, args.fps, args.show_joints)
            print()
    elif input_path.is_file() and input_path.suffix == ".hdf5":
        print(f"Rendering: {input_path}\n")
        render_episode(input_path, output_dir, args.fps, args.show_joints)
    else:
        print(f"ERROR: expected a .hdf5 file or a directory (with --all), got: {input_path}",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
