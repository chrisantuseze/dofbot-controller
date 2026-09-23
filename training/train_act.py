#!/usr/bin/env python3
"""
train_act.py
============
Trains the Language-Conditioned Action Chunking Transformer (ACT) policy
on DofBot Pro real-robot demonstration data.

Usage:
    python3 training/train_act.py \
        --dataset_dir dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset \
        --output_dir runs/act_dofbot_001 \
        --chunk_size 16 \
        --num_steps 5000 \
        --batch_size 16 \
        --lr 2e-4
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Add project root to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from training.dataset_utils import (
    DofBotDataset,
    compute_stats,
    stats_to_json,
    infinite_loader,
    IMAGE_KEY,
    STATE_KEY,
    ACTION_KEY,
    TASK_ID_KEY,
)
from inference.policy import LanguageACTPolicy


def normalize_batch(batch: dict, stats: dict, device: str) -> dict:
    """Normalize image, state, and action tensors using computed dataset stats."""
    eps = 1e-8
    out = {}

    # Image: (B, 1, 3, H, W) or (B, 3, H, W)
    img = batch[IMAGE_KEY]
    if img.dim() == 5:
        img = img.squeeze(1)
    img_mean = stats[IMAGE_KEY]["mean"].to(device)
    img_std  = stats[IMAGE_KEY]["std"].to(device)
    out[IMAGE_KEY] = (img - img_mean) / (img_std + eps)

    # State: (B, 1, 6) or (B, 6)
    state = batch[STATE_KEY]
    if state.dim() == 3:
        state = state.squeeze(1)
    state_mean = stats[STATE_KEY]["mean"].to(device)
    state_std  = stats[STATE_KEY]["std"].to(device)
    out[STATE_KEY] = (state - state_mean) / (state_std + eps)

    # Action: (B, chunk_size, 6)
    action_mean = stats[ACTION_KEY]["mean"].to(device)
    action_std  = stats[ACTION_KEY]["std"].to(device)
    out[ACTION_KEY] = (batch[ACTION_KEY] - action_mean) / (action_std + eps)

    out["action_is_pad"] = batch["action_is_pad"].to(device)
    out[TASK_ID_KEY] = batch[TASK_ID_KEY].to(device)

    return out


def train(args: argparse.Namespace):
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device(args.device)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"============================================================")
    print(f"Training Language-Conditioned ACT Policy on DofBot Pro Data")
    print(f"Device: {device} | Output Dir: {output_dir}")
    print(f"============================================================")

    # 1. Load Dataset
    dataset = DofBotDataset(
        dataset_dir=Path(args.dataset_dir),
        chunk_size=args.chunk_size,
        image_size=(args.image_size, args.image_size),
        augment=args.augment,
        preload_to_ram=True,
    )
    stats = compute_stats(dataset)

    # Save stats at root output dir
    with open(output_dir / "stats.json", "w") as fh:
        json.dump(stats_to_json(stats), fh, indent=2)

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
        drop_last=True,
    )

    # 2. Build Policy
    policy = LanguageACTPolicy(
        chunk_size=args.chunk_size,
        state_dim=6,
        action_dim=6,
        num_tasks=16,
        dim_model=args.dim_model,
        nhead=4,
        num_encoder_layers=2,
        num_decoder_layers=2,
        dim_feedforward=512,
        latent_dim=32,
        use_vae=True,
    ).to(device)

    config_dict = {
        "chunk_size": args.chunk_size,
        "state_dim": 6,
        "action_dim": 6,
        "num_tasks": 16,
        "dim_model": args.dim_model,
        "nhead": 4,
        "num_encoder_layers": 2,
        "num_decoder_layers": 2,
        "dim_feedforward": 512,
        "latent_dim": 32,
        "use_vae": True,
        "image_size": args.image_size,
    }
    with open(output_dir / "config.json", "w") as fh:
        json.dump(config_dict, fh, indent=2)

    # 3. Optimizer & Scheduler
    optimizer = torch.optim.AdamW(policy.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.num_steps, eta_min=args.lr * 0.05
    )

    # 4. Training Loop
    policy.train()
    data_iter = infinite_loader(loader)
    step = 0
    t_start = time.time()

    print(f"\nStarting training for {args.num_steps} steps (Batch: {args.batch_size}, Chunk: {args.chunk_size})...")
    print(f"{'Step':>7} | {'Total Loss':>10} | {'L1 Loss':>9} | {'L2 Loss':>9} | {'KL Loss':>8} | {'Elapsed':>8}")
    print("-" * 65)

    while step < args.num_steps:
        batch = next(data_iter)
        batch = {k: (v.to(device) if isinstance(v, torch.Tensor) else v) for k, v in batch.items()}
        batch = normalize_batch(batch, stats, device)

        optimizer.zero_grad()
        loss, loss_dict = policy(batch)
        loss.backward()
        nn.utils.clip_grad_norm_(policy.parameters(), max_norm=5.0)
        optimizer.step()
        scheduler.step()

        step += 1

        if step % args.print_freq == 0 or step == 1:
            elapsed = time.time() - t_start
            print(
                f"{step:7d} | {loss_dict['loss']:10.5f} | "
                f"{loss_dict['l1_loss']:9.5f} | {loss_dict['l2_loss']:9.5f} | "
                f"{loss_dict['kl_loss']:8.4f} | {elapsed:7.1f}s"
            )

        if step % args.save_freq == 0 or step == args.num_steps:
            ckpt_dir = output_dir / "checkpoints" / f"step_{step:06d}"
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            torch.save(policy.state_dict(), ckpt_dir / "model.pt")
            with open(ckpt_dir / "config.json", "w") as fh:
                json.dump(config_dict, fh, indent=2)
            with open(ckpt_dir / "stats.json", "w") as fh:
                json.dump(stats_to_json(stats), fh, indent=2)
            print(f"  --> Saved checkpoint: {ckpt_dir}")

    print(f"\nTraining Complete in {time.time() - t_start:.1f}s!")
    print(f"Final model checkpoint saved at: {output_dir / 'checkpoints' / f'step_{step:06d}'}")


def parse_args():
    parser = argparse.ArgumentParser(description="Train Language ACT Policy on DofBot Demonstrations")
    parser.add_argument("--dataset_dir", default="dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset")
    parser.add_argument("--output_dir", default="runs/act_dofbot_001")
    parser.add_argument("--chunk_size", type=int, default=16)
    parser.add_argument("--image_size", type=int, default=224)
    parser.add_argument("--dim_model", type=int, default=256)
    parser.add_argument("--num_steps", type=int, default=3000)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--save_freq", type=int, default=1000)
    parser.add_argument("--print_freq", type=int, default=100)
    parser.add_argument("--augment", action="store_true", default=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args()


if __name__ == "__main__":
    train(parse_args())
