#!/usr/bin/env python3

import math
import re
import h5py
from pathlib import Path
from typing import Iterator
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

# ── Constants ──────────────────────────────────────────────────────────────────

JOINT_NAMES  = ["Arm1_Joint", "Arm2_Joint", "Arm3_Joint",
                 "Arm4_Joint", "Arm5_Joint", "grip_joint"]
NUM_JOINTS   = 6
IMAGE_KEY    = "observation.images.top"
STATE_KEY    = "observation.state"
ACTION_KEY   = "action"


# ── Dataset ────────────────────────────────────────────────────────────────────

class DofBotDataset(Dataset):
    """
    Loads all HDF5 episodes into RAM and exposes one training sample per
    valid frame.

    Each sample contains:
        observation.images.top : (1, C, H, W)  float32  [0, 1]
        observation.state      : (1, state_dim) float32  radians
        action                 : (chunk_size, action_dim) float32  radians

    The action chunk at frame t is  actions[t : t + chunk_size].
    If t + chunk_size exceeds the episode length the chunk is padded by
    repeating the last recorded action.
    """

    def __init__(
        self,
        dataset_dir: Path,
        chunk_size: int = 20,
        n_obs_steps: int = 1,
        image_size: tuple[int, int] = (224, 224),
    ):
        self.chunk_size  = chunk_size
        self.n_obs_steps = n_obs_steps
        self.image_size  = image_size

        # ── Load episodes ─────────────────────────────────────────────────────
        pattern = re.compile(r"episode_(\d{6})\.hdf5$")
        eps_paths = sorted(
            [p for p in dataset_dir.iterdir() if pattern.match(p.name)],
            key=lambda p: int(pattern.match(p.name).group(1)),
        )
        if not eps_paths:
            raise FileNotFoundError(
                f"No episode_XXXXXX.hdf5 files found in {dataset_dir}"
            )

        print(f"Loading {len(eps_paths)} episode(s) from {dataset_dir}…")
        self.episodes: list[dict] = []
        for ep_path in eps_paths:
            with h5py.File(ep_path, "r") as f:
                images  = f["observation/images/top"][()]  # (T, H, W, 3) uint8 RGB
                states  = f["observation/state"][()]        # (T, 6) float32
                actions = f["action"][()]                   # (T, 6) float32
                fps     = float(f.attrs["fps"])

            T = images.shape[0]
            print(f"  {ep_path.name}: {T} frames @ {fps} fps")

            # Resize if needed (should already be the target size)
            if images.shape[1:3] != image_size:
                import cv2
                resized = np.stack(
                    [cv2.resize(img, (image_size[1], image_size[0])) for img in images]
                )
                images = resized

            # Convert images: (T, H, W, 3) uint8 → (T, 3, H, W) float32 [0,1]
            images_f = (
                images.astype(np.float32) / 255.0
            ).transpose(0, 3, 1, 2)  # (T, C, H, W)

            self.episodes.append({
                "images":  images_f,   # (T, 3, H, W) float32
                "states":  states,     # (T, 6)       float32
                "actions": actions,    # (T, 6)       float32
                "length":  T,
            })

        # ── Build flat index: (episode_idx, frame_idx) for every valid t ─────
        # "Valid" = we have at least n_obs_steps preceding frames available
        self.samples: list[tuple[int, int]] = []
        for ep_i, ep in enumerate(self.episodes):
            T = ep["length"]
            # start from n_obs_steps-1 so we always have a full obs window
            for t in range(n_obs_steps - 1, T):
                self.samples.append((ep_i, t))

        total_frames = sum(ep["length"] for ep in self.episodes)
        print(f"Dataset ready: {total_frames} total frames, "
              f"{len(self.samples)} training samples "
              f"(chunk_size={chunk_size}, n_obs_steps={n_obs_steps})")

    # ------------------------------------------------------------------
    # PyTorch Dataset interface
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict:
        ep_i, t = self.samples[idx]
        ep = self.episodes[ep_i]
        T  = ep["length"]

        # ── Observation window: [t - n_obs_steps + 1, t] ─────────────────────
        obs_start = t - self.n_obs_steps + 1
        images_obs = ep["images"][obs_start : t + 1]   # (n_obs, C, H, W)
        states_obs = ep["states"][obs_start : t + 1]   # (n_obs, 6)

        # ── Action chunk: [t, t + chunk_size) with end-padding ───────────────
        action_end    = min(t + self.chunk_size, T)
        actions_chunk = ep["actions"][t:action_end]           # (≤chunk_size, 6)
        pad_len = self.chunk_size - actions_chunk.shape[0]
        if pad_len > 0:
            last_action  = ep["actions"][-1:].repeat(pad_len, axis=0)
            actions_chunk = np.concatenate([actions_chunk, last_action], axis=0)

        # Boolean mask: True where action step was padded (not real data)
        is_pad = np.zeros(self.chunk_size, dtype=bool)
        if pad_len > 0:
            is_pad[-pad_len:] = True

        return {
            IMAGE_KEY:        torch.from_numpy(images_obs),           # (1, C, H, W)
            STATE_KEY:        torch.from_numpy(states_obs),           # (1, 6)
            ACTION_KEY:       torch.from_numpy(actions_chunk),        # (chunk_size, 6)
            "action_is_pad":  torch.from_numpy(is_pad),               # (chunk_size,) bool
        }


# ── Statistics utilities ───────────────────────────────────────────────────────

def compute_stats(dataset: DofBotDataset) -> dict[str, dict[str, torch.Tensor]]:
    """
    Compute mean / std / min / max over the full dataset for state, action,
    and image features.  Used to initialise the policy's normalisation layers.

    Image stats are shaped (3, 1, 1) for channel-wise broadcasting.
    """
    all_states  = np.concatenate([ep["states"]  for ep in dataset.episodes], axis=0)
    all_actions = np.concatenate([ep["actions"] for ep in dataset.episodes], axis=0)
    # Images are already (T, 3, H, W) float32
    all_imgs = np.concatenate([ep["images"] for ep in dataset.episodes], axis=0)
    imgs_flat = all_imgs.reshape(all_imgs.shape[0], 3, -1)   # (N, 3, H*W)

    def t(arr): return torch.from_numpy(arr.astype(np.float32))

    img_mean = imgs_flat.mean(axis=(0, 2)).reshape(3, 1, 1)
    img_std  = imgs_flat.std(axis=(0, 2)).reshape(3, 1, 1)
    img_min  = imgs_flat.min(axis=(0, 2)).reshape(3, 1, 1)
    img_max  = imgs_flat.max(axis=(0, 2)).reshape(3, 1, 1)

    return {
        IMAGE_KEY: {
            "mean": t(img_mean),
            "std":  t(img_std),
            "min":  t(img_min),
            "max":  t(img_max),
        },
        STATE_KEY: {
            "mean": t(all_states.mean(axis=0)),
            "std":  t(all_states.std(axis=0)),
            "min":  t(all_states.min(axis=0)),
            "max":  t(all_states.max(axis=0)),
        },
        ACTION_KEY: {
            "mean": t(all_actions.mean(axis=0)),
            "std":  t(all_actions.std(axis=0)),
            "min":  t(all_actions.min(axis=0)),
            "max":  t(all_actions.max(axis=0)),
        },
    }


def stats_to_json(stats: dict) -> dict:
    """Serialise stats dict (torch.Tensors) to JSON-compatible nested lists."""
    out = {}
    for feat, d in stats.items():
        out[feat] = {k: v.tolist() for k, v in d.items()}
    return out


def stats_from_json(d: dict) -> dict:
    """Deserialise stats dict from JSON back to torch.Tensors."""
    out = {}
    for feat, vals in d.items():
        out[feat] = {k: torch.tensor(v) for k, v in vals.items()}
    return out


# ── Infinite dataloader helper ─────────────────────────────────────────────────

def infinite_loader(loader: DataLoader) -> Iterator[dict]:
    while True:
        yield from loader