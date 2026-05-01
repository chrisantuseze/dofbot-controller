#!/usr/bin/env python3
"""
replay_episode.py
=================
Replay an HDF5 episode by writing:
  1. An MP4 video of the camera frames (with frame counter + joint angles
     overlaid).
  2. A PNG plot of the joint state and action trajectories.

Usage
-----
    # Single episode
    conda run -n dofbot_controller python3 tools/replay_episode.py \
        dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000019.hdf5

    # Custom output directory
    conda run -n dofbot_controller python3 tools/replay_episode.py \
        dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000019.hdf5 \
        --output_dir /tmp/replay_ep19

    # Slower playback (write 10 fps instead of native fps)
    conda run -n dofbot_controller python3 tools/replay_episode.py \
        dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset/episode_000019.hdf5 \
        --fps 10

Outputs
-------
    <output_dir>/
        video.mp4            ← camera replay with overlay
        joints_plot.png      ← 6-panel state vs action trajectory plot
        episode_data.jsonl   ← per-frame state/action (for further analysis)
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

JOINT_NAMES = ["Arm1", "Arm2", "Arm3", "Arm4", "Arm5", "Gripper"]


def load_episode(hdf5_path: Path) -> dict:
    with h5py.File(hdf5_path, "r") as f:
        images      = f["observation/images/top"][()]   # (T, H, W, 3) uint8 RGB
        states      = f["observation/state"][()]        # (T, 6) float32 rad
        actions     = f["action"][()]                   # (T, 6) float32 rad
        fps         = float(f.attrs.get("fps", 10))
        ep_idx      = int(f.attrs.get("episode_index", -1))
        num_frames  = int(f.attrs.get("num_frames", images.shape[0]))
        task        = f.attrs.get("task", b"").decode() if isinstance(
                          f.attrs.get("task", ""), bytes
                      ) else str(f.attrs.get("task", ""))
        obj_label   = f.attrs.get("object_label", b"").decode() if isinstance(
                          f.attrs.get("object_label", ""), bytes
                      ) else str(f.attrs.get("object_label", ""))
    return dict(images=images, states=states, actions=actions, fps=fps,
                episode_index=ep_idx, num_frames=num_frames,
                task=task, object_label=obj_label)


def write_video(images: np.ndarray, states: np.ndarray, fps: float,
                out_path: Path, episode_index: int, task: str) -> None:
    """Write annotated MP4 using OpenCV VideoWriter (no ffmpeg required)."""
    T, H, W, _ = images.shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (W, H))

    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    thickness  = 1
    color_white = (255, 255, 255)
    color_bg    = (0, 0, 0)

    for t in range(T):
        frame = images[t].copy()          # RGB uint8
        bgr   = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # ── Overlay ──────────────────────────────────────────────────────────
        # Episode + frame counter
        cv2.putText(bgr, f"ep={episode_index:04d}  t={t:04d}/{T-1:04d}",
                    (4, 14), font, font_scale, color_bg, thickness + 1,
                    cv2.LINE_AA)
        cv2.putText(bgr, f"ep={episode_index:04d}  t={t:04d}/{T-1:04d}",
                    (4, 14), font, font_scale, color_white, thickness,
                    cv2.LINE_AA)

        # Task label (first 50 chars)
        if task:
            label = task[:50]
            cv2.putText(bgr, label, (4, 28), font, font_scale, color_bg,
                        thickness + 1, cv2.LINE_AA)
            cv2.putText(bgr, label, (4, 28), font, font_scale, color_white,
                        thickness, cv2.LINE_AA)

        # Joint states (radians, 2 decimal places)
        s = states[t]
        jtext = "  ".join(f"{v:+.2f}" for v in s)
        cv2.putText(bgr, jtext, (4, H - 8), font, 0.35, color_bg,
                    thickness + 1, cv2.LINE_AA)
        cv2.putText(bgr, jtext, (4, H - 8), font, 0.35, color_white,
                    thickness, cv2.LINE_AA)

        writer.write(bgr)

    writer.release()
    print(f"Video  → {out_path}  ({T} frames @ {fps:.1f} fps)")


def write_joint_plot(states: np.ndarray, actions: np.ndarray,
                     fps: float, out_path: Path, task: str) -> None:
    """6-panel plot: state (blue) vs commanded action (orange) per joint."""
    T = states.shape[0]
    t_axis = np.arange(T) / fps   # seconds

    fig, axes = plt.subplots(6, 1, figsize=(12, 14), sharex=True)
    fig.suptitle(
        f"Episode joint trajectories\nTask: {task}" if task else
        "Episode joint trajectories",
        fontsize=11,
    )

    for i, (ax, name) in enumerate(zip(axes, JOINT_NAMES)):
        ax.plot(t_axis, states[:, i],  label="state",  linewidth=1.2)
        ax.plot(t_axis, actions[:, i], label="action", linewidth=1.2,
                linestyle="--", alpha=0.8)
        ax.set_ylabel(f"{name}\n(rad)", fontsize=8)
        ax.legend(fontsize=7, loc="upper right")
        ax.grid(True, linewidth=0.4)

    axes[-1].set_xlabel("Time (s)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Plot   → {out_path}")


def write_jsonl(states: np.ndarray, actions: np.ndarray,
                out_path: Path) -> None:
    """Write per-frame state/action as JSONL for further analysis."""
    with open(out_path, "w") as fh:
        for t in range(states.shape[0]):
            fh.write(json.dumps({
                "t":      t,
                "state":  states[t].tolist(),
                "action": actions[t].tolist(),
            }) + "\n")
    print(f"JSONL  → {out_path}  ({states.shape[0]} frames)")


def replay(hdf5_path: Path, output_dir: Path, override_fps: float | None) -> None:
    ep = load_episode(hdf5_path)
    fps = override_fps if override_fps else ep["fps"]

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nEpisode {ep['episode_index']:04d}  |  {ep['num_frames']} frames "
          f"@ {ep['fps']:.1f} fps  |  task: {ep['task'] or '(none)'}")
    print(f"Output → {output_dir}\n")

    write_video(
        ep["images"], ep["states"], fps,
        output_dir / "video.mp4",
        ep["episode_index"], ep["task"],
    )
    write_joint_plot(
        ep["states"], ep["actions"], fps,
        output_dir / "joints_plot.png",
        ep["task"],
    )
    write_jsonl(
        ep["states"], ep["actions"],
        output_dir / "episode_data.jsonl",
    )
    print("\nDone.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay a DofBot episode HDF5 file to video + joint plot.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("hdf5_path", help="Path to episode_XXXXXX.hdf5")
    parser.add_argument(
        "--output_dir", default=None,
        help="Directory to write outputs. Default: <hdf5_dir>/<episode_stem>_replay/",
    )
    parser.add_argument(
        "--fps", default=None, type=float,
        help="Override playback fps (default: use fps stored in the HDF5 file)",
    )
    args = parser.parse_args()

    hdf5_path = Path(args.hdf5_path).resolve()
    if not hdf5_path.exists():
        print(f"Error: file not found: {hdf5_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else hdf5_path.parent / (hdf5_path.stem + "_replay")
    )

    replay(hdf5_path, output_dir, args.fps)


if __name__ == "__main__":
    main()
