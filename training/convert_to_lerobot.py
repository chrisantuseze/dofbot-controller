#!/usr/bin/env python3
"""
convert_to_lerobot.py
=====================
Converts DofBot Pro HDF5 episode files → LeRobot v2.0 dataset format so
the dataset can be used directly with the LeRobot training machinery.

Input  – directory containing episode_XXXXXX.hdf5 files
         (produced by dofbot_policy_bridge/scripts/data_collector.py)

Output – LeRobot v2 dataset directory with the structure:
    <output_dir>/
        data/chunk-000/episode_000000.parquet   ← state + action columns
        data/chunk-000/episode_000001.parquet
        videos/chunk-000/observation.images.top/episode_000000.mp4
        videos/chunk-000/observation.images.top/episode_000001.mp4
        meta/info.json
        meta/episodes.jsonl
        meta/tasks.jsonl
        meta/stats.json

Usage
-----
    python convert_to_lerobot.py \\
        dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset \\
        /tmp/dofbot_lerobot_dataset \\
        --task "pick and place red cube"

Dependencies (no lerobot install required):
    pip install h5py numpy pyarrow
    apt install ffmpeg   # or brew install ffmpeg
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import h5py
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# ── Constants matching data_collector.py ──────────────────────────────────────

JOINT_NAMES = [
    "Arm1_Joint", "Arm2_Joint", "Arm3_Joint",
    "Arm4_Joint", "Arm5_Joint", "grip_joint",
]
CHUNKS_SIZE = 1000   # max episodes per chunk sub-directory


# ── Episode discovery ──────────────────────────────────────────────────────────

def find_hdf5_episodes(input_dir: Path) -> list[Path]:
    """Return HDF5 episode files sorted by episode index."""
    pattern = re.compile(r"episode_(\d{6})\.hdf5$")
    eps = sorted(
        [p for p in input_dir.iterdir() if pattern.match(p.name)],
        key=lambda p: int(pattern.match(p.name).group(1)),
    )
    if not eps:
        raise FileNotFoundError(
            f"No episode_XXXXXX.hdf5 files found in {input_dir}"
        )
    return eps


# ── Video encoding ─────────────────────────────────────────────────────────────

def encode_video(images: np.ndarray, out_path: Path, fps: float) -> dict:
    """
    Encode (T, H, W, 3) uint8 RGB array to MP4 using ffmpeg.

    Returns the video info dict written into meta/info.json.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    T, H, W, _C = images.shape

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "pipe:0",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        "-an",          # no audio stream
        str(out_path),
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proc.stdin.write(images.tobytes())
    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(
            f"ffmpeg exited with code {rc} while encoding {out_path}. "
            "Is ffmpeg installed? (apt install ffmpeg)"
        )

    return {
        "video.fps": float(fps),
        "video.codec": "libx264",
        "video.pix_fmt": "yuv420p",
        "video.is_depth_map": False,
        "has_audio": False,
    }


# ── Parquet serialisation ──────────────────────────────────────────────────────

def write_parquet(
    out_path: Path,
    ep_idx: int,
    states: np.ndarray,    # (T, 6)  float32
    actions: np.ndarray,   # (T, 6)  float32
    fps: float,
    global_index_offset: int,
    task_index: int = 0,
) -> None:
    """Write one parquet file for a single episode."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    T = states.shape[0]

    timestamps    = (np.arange(T, dtype=np.float64) / fps)
    frame_indices = np.arange(T, dtype=np.int64)
    global_idx    = np.arange(global_index_offset, global_index_offset + T, dtype=np.int64)
    ep_col        = np.full(T, ep_idx, dtype=np.int64)
    task_col      = np.full(T, task_index, dtype=np.int64)
    next_done     = np.zeros(T, dtype=bool)
    next_done[-1] = True

    table = pa.table({
        "observation.state": pa.array(states.tolist(),  type=pa.list_(pa.float32())),
        "action":            pa.array(actions.tolist(), type=pa.list_(pa.float32())),
        "timestamp":         pa.array(timestamps,       type=pa.float64()),
        "frame_index":       pa.array(frame_indices,    type=pa.int64()),
        "episode_index":     pa.array(ep_col,           type=pa.int64()),
        "index":             pa.array(global_idx,       type=pa.int64()),
        "task_index":        pa.array(task_col,         type=pa.int64()),
        "next.done":         pa.array(next_done,        type=pa.bool_()),
    })
    pq.write_table(table, out_path)


# ── Statistics ─────────────────────────────────────────────────────────────────

def compute_dataset_stats(
    all_states: np.ndarray,    # (N, 6)
    all_actions: np.ndarray,   # (N, 6)
    all_images: np.ndarray,    # (N, H, W, 3) uint8
) -> dict:
    """
    Compute mean / std / min / max for each feature.

    Images are analysed in [0, 1] float space.
    Image stats are shaped (3, 1, 1) for channel-wise broadcasting.
    """

    def vec_stats(arr: np.ndarray) -> dict:
        return {
            "mean": arr.mean(axis=0).tolist(),
            "std":  arr.std(axis=0).tolist(),
            "min":  arr.min(axis=0).tolist(),
            "max":  arr.max(axis=0).tolist(),
        }

    imgs_f   = all_images.astype(np.float32) / 255.0     # (N, H, W, 3)
    imgs_flat = imgs_f.reshape(-1, 3)                     # (N*H*W, 3)

    # Reshape to (3, 1, 1) so the stats can be broadcast over C×H×W tensors
    img_stats = {}
    for stat_name, fn in [("mean", np.mean), ("std", np.std),
                           ("min", np.min), ("max", np.max)]:
        val = fn(imgs_flat, axis=0)          # (3,)
        img_stats[stat_name] = val.reshape(3, 1, 1).tolist()

    return {
        "observation.state":      vec_stats(all_states),
        "action":                 vec_stats(all_actions),
        "observation.images.top": img_stats,
    }


# ── Main conversion ────────────────────────────────────────────────────────────

def convert(input_dir: Path, output_dir: Path, task: str) -> None:
    episode_paths = find_hdf5_episodes(input_dir)
    n_episodes = len(episode_paths)
    print(f"Found {n_episodes} episode(s) in {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    all_states:  list[np.ndarray] = []
    all_actions: list[np.ndarray] = []
    all_images:  list[np.ndarray] = []
    episodes_meta: list[dict]     = []
    total_frames  = 0
    video_info    = None
    fps           = None

    for ep_path in episode_paths:
        with h5py.File(ep_path, "r") as f:
            ep_idx   = int(f.attrs["episode_index"])
            fps      = float(f.attrs["fps"])
            n_frames = int(f.attrs["num_frames"])
            images   = f["observation/images/top"][()]  # (T, H, W, 3) uint8 RGB
            states   = f["observation/state"][()]        # (T, 6) float32
            actions  = f["action"][()]                   # (T, 6) float32

        print(f"  episode_{ep_idx:06d}: {n_frames} frames @ {fps} fps "
              f"| image {images.shape[1]}×{images.shape[2]}")

        chunk = ep_idx // CHUNKS_SIZE

        # ── Video ─────────────────────────────────────────────────────────────
        vid_path = (
            output_dir / "videos"
            / f"chunk-{chunk:03d}"
            / "observation.images.top"
            / f"episode_{ep_idx:06d}.mp4"
        )
        vinfo = encode_video(images, vid_path, fps)
        if video_info is None:
            video_info = vinfo

        # ── Parquet ───────────────────────────────────────────────────────────
        parquet_path = (
            output_dir / "data"
            / f"chunk-{chunk:03d}"
            / f"episode_{ep_idx:06d}.parquet"
        )
        write_parquet(parquet_path, ep_idx, states, actions, fps, total_frames)

        # ── Accumulate for stats ──────────────────────────────────────────────
        all_states.append(states)
        all_actions.append(actions)
        all_images.append(images)
        episodes_meta.append({
            "episode_index": ep_idx,
            "tasks": [task],
            "length": n_frames,
        })
        total_frames += n_frames

    # ── Dataset statistics ────────────────────────────────────────────────────
    print("Computing dataset statistics…")
    all_states_np  = np.concatenate(all_states,  axis=0)
    all_actions_np = np.concatenate(all_actions, axis=0)
    all_images_np  = np.concatenate(all_images,  axis=0)
    stats = compute_dataset_stats(all_states_np, all_actions_np, all_images_np)

    # ── meta/ files ───────────────────────────────────────────────────────────
    meta_dir = output_dir / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)

    H, W = all_images_np.shape[1:3]
    info = {
        "codebase_version": "v2.0",
        "robot_type": "dofbot_pro",
        "fps": fps,
        "features": {
            "observation.state": {
                "dtype": "float32",
                "shape": [6],
                "names": JOINT_NAMES,
            },
            "action": {
                "dtype": "float32",
                "shape": [6],
                "names": JOINT_NAMES,
            },
            "observation.images.top": {
                "dtype": "video",
                "shape": [3, H, W],
                "names": ["channel", "height", "width"],
                "info": video_info,
            },
            "timestamp":     {"dtype": "float32", "shape": [1], "names": None},
            "frame_index":   {"dtype": "int64",   "shape": [1], "names": None},
            "episode_index": {"dtype": "int64",   "shape": [1], "names": None},
            "index":         {"dtype": "int64",   "shape": [1], "names": None},
            "task_index":    {"dtype": "int64",   "shape": [1], "names": None},
            "next.done":     {"dtype": "bool",    "shape": [1], "names": None},
        },
        "total_episodes":  n_episodes,
        "total_frames":    total_frames,
        "total_tasks":     1,
        "total_videos":    n_episodes,
        "total_chunks":    1,
        "chunks_size":     CHUNKS_SIZE,
        "splits":          {"train": f"0:{n_episodes}"},
        # Template strings for path resolution (LeRobot convention)
        "data_path":  "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet",
        "video_path": "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        "tasks":      [{"task_index": 0, "task": task}],
    }

    with open(meta_dir / "info.json", "w") as fh:
        json.dump(info, fh, indent=2)

    with open(meta_dir / "episodes.jsonl", "w") as fh:
        for em in episodes_meta:
            fh.write(json.dumps(em) + "\n")

    with open(meta_dir / "stats.json", "w") as fh:
        json.dump(stats, fh, indent=2)

    with open(meta_dir / "tasks.jsonl", "w") as fh:
        fh.write(json.dumps({"task_index": 0, "task": task}) + "\n")

    print(f"\nConversion complete!")
    print(f"  Output path : {output_dir}")
    print(f"  Episodes    : {n_episodes}")
    print(f"  Total frames: {total_frames}")
    print(f"  FPS         : {fps}")
    print(f"\nNext step:")
    print(f"  python train_act.py --dataset_dir {input_dir} --output_dir runs/act_001")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert DofBot Pro HDF5 episodes to LeRobot v2 dataset format.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_dir",
        help="Directory containing episode_XXXXXX.hdf5 files",
    )
    parser.add_argument(
        "output_dir",
        help="Destination directory for the LeRobot dataset",
    )
    parser.add_argument(
        "--task",
        default="robot manipulation",
        help="Human-readable task description stored in the dataset metadata",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Validate ffmpeg is available before touching any files
    if subprocess.run(["ffmpeg", "-version"],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL).returncode != 0:
        print("ERROR: ffmpeg not found. Install it with:  apt install ffmpeg",
              file=sys.stderr)
        sys.exit(1)

    convert(Path(args.input_dir), Path(args.output_dir), args.task)
