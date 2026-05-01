import h5py
import json
import numpy as np
from PIL import Image
from pathlib import Path
import sys
from typing import List, Dict

def find_episodes(dataset_dir: str) -> List[Path]:
    """Find all episode HDF5 files in a directory, sorted by episode number."""
    dataset_path = Path(dataset_dir)
    episodes = sorted(dataset_path.glob("episode_*.hdf5"))
    return episodes

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
        task          = f.attrs.get("task", "")
        object_label  = f.attrs.get("object_label", "")

        if isinstance(task, bytes):
            task = task.decode("utf-8")
        if isinstance(object_label, bytes):
            object_label = object_label.decode("utf-8")

        print(f"Episode {episode_index:06d}  |  robot={robot}  |  "
              f"fps={fps}  |  frames={num_frames}")
        print(f"Joint names: {joint_names}\n")
        if task:
            print(f"Task: {task}")
        if object_label:
            print(f"Object label: {object_label}")

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


def read_all_episodes(dataset_dir: str, output_base_dir: str = None):
    """Read all episodes in a dataset directory."""
    episodes = find_episodes(dataset_dir)
    
    if not episodes:
        print(f"No episode files found in {dataset_dir}")
        return
    
    print(f"Found {len(episodes)} episodes\n")
    print("=" * 80)
    
    all_data = []
    for ep_path in episodes:
        out = None
        if output_base_dir:
            out = Path(output_base_dir) / ep_path.stem
        
        data = read_episode(str(ep_path), output_dir=out, save_images=True)
        all_data.append(data)
        print("=" * 80)
    
    return all_data


if __name__ == "__main__":
    # Parse command-line arguments
    if len(sys.argv) < 2:
        # Default to reading from dofbot_dataset in the current directory
        dataset_dir = "dofbot_dataset"
        output_base_dir = None
        
        if not Path(dataset_dir).exists():
            print("Usage: python read_episode.py [episode_file.hdf5 | dataset_dir] [output_dir]")
            print("\nExamples:")
            print("  python read_episode.py                              # Read all from dofbot_dataset")
            print("  python read_episode.py episode_000000.hdf5          # Read single episode")
            print("  python read_episode.py /path/to/dataset             # Read all from dataset dir")
            print("  python read_episode.py episode_000000.hdf5 /output  # Read single episode to output dir")
            sys.exit(1)
        
        read_all_episodes(dataset_dir, output_base_dir)
    else:
        input_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
        
        input_path_obj = Path(input_path)
        
        # Check if it's an episode file
        if input_path_obj.is_file() and input_path_obj.suffix == ".hdf5":
            read_episode(str(input_path_obj), output_dir=output_dir, save_images=True)
        # Check if it's a directory
        elif input_path_obj.is_dir():
            read_all_episodes(input_path, output_dir)
        else:
            print(f"Error: Path not found or not a valid episode file: {input_path}")
            print("Usage: python read_episode.py [episode_file.hdf5 | dataset_dir] [output_dir]")
            sys.exit(1)