import h5py
import json
import numpy as np
from PIL import Image
from pathlib import Path
import sys

def read_episode(hdf5_path: str, output_dir: str = None, save_images: bool = True):
    """
    Reader for DofBot Pro episode files saved by _save_episode().

    Schema:
        observation/images/top  (T, H, W, 3)  uint8, lzf-compressed
        observation/state       (T, 6)         float, joint positions
        action                  (T, 6)         float, joint commands
        attrs: fps, episode_index, num_frames, robot, joint_names
    """
    path = Path(hdf5_path)
    out  = Path(output_dir) if output_dir else path.parent / (path.stem + "_frames")

    with h5py.File(hdf5_path, "r") as f:

        # ── Metadata ──────────────────────────────────────────────────────────
        fps           = f.attrs["fps"]
        episode_index = f.attrs["episode_index"]
        num_frames    = f.attrs["num_frames"]
        robot         = f.attrs["robot"]
        joint_names   = list(f.attrs["joint_names"])

        print(f"Episode {episode_index:06d}  |  robot={robot}  |  "
              f"fps={fps}  |  frames={num_frames}")
        print(f"Joint names: {joint_names}\n")

        # ── Load arrays ───────────────────────────────────────────────────────
        images  = f["observation/images/top"][()]   # (T, H, W, 3)
        states  = f["observation/state"][()]        # (T, 6)
        actions = f["action"][()]                   # (T, 6)

    T = images.shape[0]
    assert T == num_frames, f"Frame count mismatch: array has {T}, attr says {num_frames}"

    # ── Print state / action table ────────────────────────────────────────────
    header = f"{'t':>5}  " + \
             "  ".join(f"{'s_'+n:>10}" for n in joint_names) + "  |  " + \
             "  ".join(f"{'a_'+n:>10}" for n in joint_names)
    # print(header)
    # print("-" * len(header))

    # for t in range(T):
    #     s_str = "  ".join(f"{v:>10.4f}" for v in states[t])
    #     a_str = "  ".join(f"{v:>10.4f}" for v in actions[t])
    #     print(f"{t:>5}  {s_str}  |  {a_str}")

    # ── Write state / action JSONL ────────────────────────────────────────────
    jsonl_path = path.parent / (path.stem + "_data.jsonl")
    with open(jsonl_path, "w") as jf:
        for t in range(T):
            record = {
                "t": t,
                "state":  states[t].tolist(),
                "action": actions[t].tolist(),
            }
            jf.write(json.dumps(record) + "\n")
    print(f"\n{T} timesteps written to: {jsonl_path.resolve()}")

    # ── Save frames to disk ───────────────────────────────────────────────────
    if save_images:
        out.mkdir(parents=True, exist_ok=True)
        for t, frame in enumerate(images):
            Image.fromarray(frame).save(out / f"frame_{t:05d}.png")
        print(f"{T} frames written to: {out.resolve()}")

    return {
        "images":       images,
        "states":       states,
        "actions":      actions,
        "joint_names":  joint_names,
        "fps":          fps,
        "episode_index": episode_index,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_episode.py <episode_XXXXXX.hdf5> [output_dir]")
        sys.exit(1)

    out = sys.argv[2] if len(sys.argv) > 2 else None
    read_episode(sys.argv[1], output_dir=out)