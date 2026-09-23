#!/usr/bin/env python3
"""
dataset_utils.py
================
Dataset loader and preprocessing utilities for DofBot Pro demonstration episodes.

Handles:
- Loading HDF5 episodes with images, joint states, actions, and language metadata.
- Language command parsing and tokenization.
- Action chunking with causal horizon H and padding masks.
- Dataset normalization statistics computation (mean/std/min/max).
- Data augmentation for camera images and robot states.
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import h5py
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

# ── Keys & Constants ─────────────────────────────────────────────────────────
IMAGE_KEY   = "observation.images.top"
STATE_KEY   = "observation.state"
ACTION_KEY  = "action"
LANG_KEY    = "language_instruction"
TASK_ID_KEY = "task_id"

NUM_JOINTS = 6

# Canonical task vocabulary for Verify2Act grasping
CANONICAL_TASKS = [
    "pick and place red cube to side area",
    "pick and place blue cube to side area",
    "pick and place green cube to side area",
    "pick and place yellow cube to side area",
    "pick and place multi-color cube to side area",
    "grasp red cube",
    "grasp blue cube",
    "grasp green cube",
    "grasp yellow cube",
    "clear red obstacle",
    "clear blue obstacle",
    "clear green obstacle",
    "clear yellow obstacle",
]

TASK_TO_ID = {task: idx for idx, task in enumerate(CANONICAL_TASKS)}


def text_to_task_id(text: str) -> int:
    """Map arbitrary natural language instruction to canonical task ID."""
    text_lower = text.lower().strip()
    if text_lower in TASK_TO_ID:
        return TASK_TO_ID[text_lower]
    
    # Fuzzy matching based on keywords
    if "red" in text_lower:
        return TASK_TO_ID["pick and place red cube to side area"]
    elif "blue" in text_lower:
        return TASK_TO_ID["pick and place blue cube to side area"]
    elif "green" in text_lower:
        return TASK_TO_ID["pick and place green cube to side area"]
    elif "yellow" in text_lower:
        return TASK_TO_ID["pick and place yellow cube to side area"]
    elif "multi" in text_lower or "color" in text_lower:
        return TASK_TO_ID["pick and place multi-color cube to side area"]
    
    return 0


# ── Statistics helpers ───────────────────────────────────────────────────────

def stats_to_json(stats: Dict) -> Dict:
    """Convert torch/numpy stats dictionary to serializable plain JSON dict."""
    serializable = {}
    for k, v in stats.items():
        if isinstance(v, dict):
            serializable[k] = stats_to_json(v)
        elif isinstance(v, (torch.Tensor, np.ndarray)):
            serializable[k] = v.tolist()
        elif isinstance(v, (int, float, str, bool)):
            serializable[k] = v
        else:
            serializable[k] = str(v)
    return serializable


def stats_from_json(json_dict: Dict, device: str = "cpu") -> Dict:
    """Convert JSON stats back to torch tensors on specified device."""
    stats = {}
    for k, v in json_dict.items():
        if isinstance(v, dict):
            stats[k] = stats_from_json(v, device=device)
        elif isinstance(v, list):
            stats[k] = torch.tensor(v, dtype=torch.float32, device=device)
        else:
            stats[k] = v
    return stats


# ── DofBotDataset ────────────────────────────────────────────────────────────

class DofBotDataset(Dataset):
    """
    PyTorch Dataset for DofBot Pro HDF5 demonstrations.
    
    Returns sample dictionary:
        - observation.images.top: (1, 3, H, W) float32 tensor in [0, 1]
        - observation.state:      (1, 6) float32 tensor (joint positions)
        - action:                 (chunk_size, 6) float32 tensor
        - action_is_pad:          (chunk_size,) bool tensor (True if padded past episode end)
        - language_instruction:   str
        - task_id:                int tensor
    """

    def __init__(
        self,
        dataset_dir: Union[str, Path],
        chunk_size: int = 16,
        n_obs_steps: int = 1,
        image_size: Tuple[int, int] = (224, 224),
        augment: bool = False,
        preload_to_ram: bool = False,
    ):
        super().__init__()
        self.dataset_dir = Path(dataset_dir)
        self.chunk_size = chunk_size
        self.n_obs_steps = n_obs_steps
        self.image_size = image_size
        self.augment = augment
        self.preload_to_ram = preload_to_ram

        self.episode_paths = sorted(self.dataset_dir.glob("episode_*.hdf5"))
        if not self.episode_paths:
            raise FileNotFoundError(f"No episode_*.hdf5 files found in {self.dataset_dir}")

        # Task mapping from json if present
        task_map_file = self.dataset_dir / "episode_task_map.json"
        self.task_map = {}
        if task_map_file.exists():
            with open(task_map_file, "r") as f:
                self.task_map = json.load(f)

        self.episodes = []
        self.samples = []  # list of (ep_idx, timestep)
        self._h5_handles = {}

        print(f"Indexing {len(self.episode_paths)} demonstration episodes from {self.dataset_dir}...")
        for ep_idx, ep_path in enumerate(self.episode_paths):
            with h5py.File(ep_path, "r") as f:
                num_frames = int(f.attrs.get("num_frames", f["action"].shape[0]))
                task_str = f.attrs.get("task", "")
                if isinstance(task_str, bytes):
                    task_str = task_str.decode("utf-8")
                
                # Check task_map fallback
                str_key = str(ep_idx)
                if not task_str and str_key in self.task_map:
                    task_str = self.task_map[str_key]
                if not task_str:
                    task_str = "pick and place cube to side area"

                obj_label = f.attrs.get("object_label", "")
                if isinstance(obj_label, bytes):
                    obj_label = obj_label.decode("utf-8")

                ep_data = {
                    "path": ep_path,
                    "length": num_frames,
                    "task": task_str,
                    "object_label": obj_label,
                    "task_id": text_to_task_id(task_str),
                }
                self.episodes.append(ep_data)

                for t in range(num_frames):
                    self.samples.append((ep_idx, t))

        print(f"Indexed {len(self.episodes)} episodes with total {len(self.samples)} sample transitions.")

        # Visual augmentations
        if self.augment:
            self.color_jitter = transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15)
        else:
            self.color_jitter = None

    def __len__(self) -> int:
        return len(self.samples)

    def _get_h5_handle(self, path: Path) -> h5py.File:
        str_path = str(path)
        if str_path not in self._h5_handles:
            self._h5_handles[str_path] = h5py.File(str_path, "r", swmr=True)
        return self._h5_handles[str_path]

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        ep_idx, t = self.samples[idx]
        ep = self.episodes[ep_idx]
        length = ep["length"]

        h5_f = self._get_h5_handle(ep["path"])
        raw_img = h5_f["observation/images/top"][t]       # (H, W, 3)
        raw_state = h5_f["observation/state"][t]          # (6,)
        
        # Slice action chunk [t : t + chunk_size]
        end_t = min(t + self.chunk_size, length)
        raw_actions = h5_f["action"][t:end_t]             # (K, 6)

        # Process image: (H, W, 3) uint8 -> (3, H, W) float32 [0, 1]
        img_tensor = torch.from_numpy(raw_img).permute(2, 0, 1).float() / 255.0
        if self.augment and self.color_jitter is not None:
            img_tensor = self.color_jitter(img_tensor)

        # Process state: (6,)
        state_tensor = torch.from_numpy(raw_state).float()

        # Action chunking & padding
        act_len = raw_actions.shape[0]
        action_chunk = np.zeros((self.chunk_size, NUM_JOINTS), dtype=np.float32)
        action_is_pad = np.zeros((self.chunk_size,), dtype=bool)

        action_chunk[:act_len] = raw_actions
        if act_len < self.chunk_size:
            # Repeat last action to fill chunk
            if act_len > 0:
                action_chunk[act_len:] = raw_actions[-1]
            action_is_pad[act_len:] = True

        action_tensor = torch.from_numpy(action_chunk).float()
        pad_tensor = torch.from_numpy(action_is_pad).bool()

        return {
            IMAGE_KEY: img_tensor.unsqueeze(0),       # (1, 3, H, W)
            STATE_KEY: state_tensor.unsqueeze(0),     # (1, 6)
            ACTION_KEY: action_tensor,                # (chunk_size, 6)
            "action_is_pad": pad_tensor,              # (chunk_size,)
            LANG_KEY: ep["task"],
            TASK_ID_KEY: torch.tensor(ep["task_id"], dtype=torch.long),
        }


# ── Statistics Computation ─────────────────────────────────────────────────

def compute_stats(dataset: DofBotDataset) -> Dict[str, Dict[str, torch.Tensor]]:
    """Compute dataset normalization statistics (mean, std, min, max)."""
    all_states = []
    all_actions = []
    all_images = []

    print("Computing dataset normalization statistics...")
    for ep in dataset.episodes:
        with h5py.File(ep["path"], "r") as f:
            all_states.append(f["observation/state"][()])
            all_actions.append(f["action"][()])
            imgs = f["observation/images/top"][()]
            step = max(1, imgs.shape[0] // 10)
            all_images.append(imgs[::step])

    cat_states  = np.concatenate(all_states, axis=0)   # (Total, 6)
    cat_actions = np.concatenate(all_actions, axis=0)  # (Total, 6)
    cat_images  = np.concatenate(all_images, axis=0).astype(np.float32) / 255.0  # (Total, H, W, 3)

    # State stats
    state_mean = torch.tensor(np.mean(cat_states, axis=0), dtype=torch.float32)
    state_std  = torch.tensor(np.std(cat_states, axis=0), dtype=torch.float32)
    state_std  = torch.clamp(state_std, min=1e-3)
    state_min  = torch.tensor(np.min(cat_states, axis=0), dtype=torch.float32)
    state_max  = torch.tensor(np.max(cat_states, axis=0), dtype=torch.float32)

    # Action stats
    action_mean = torch.tensor(np.mean(cat_actions, axis=0), dtype=torch.float32)
    action_std  = torch.tensor(np.std(cat_actions, axis=0), dtype=torch.float32)
    action_std  = torch.clamp(action_std, min=1e-3)
    action_min  = torch.tensor(np.min(cat_actions, axis=0), dtype=torch.float32)
    action_max  = torch.tensor(np.max(cat_actions, axis=0), dtype=torch.float32)

    # Image stats channel-wise (3, 1, 1)
    img_mean = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(3, 1, 1)
    img_std  = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(3, 1, 1)

    stats = {
        STATE_KEY: {
            "mean": state_mean,
            "std":  state_std,
            "min":  state_min,
            "max":  state_max,
        },
        ACTION_KEY: {
            "mean": action_mean,
            "std":  action_std,
            "min":  action_min,
            "max":  action_max,
        },
        IMAGE_KEY: {
            "mean": img_mean,
            "std":  img_std,
        }
    }
    return stats


def infinite_loader(loader: DataLoader):
    """Yield batches indefinitely from a DataLoader."""
    while True:
        for batch in loader:
            yield batch
