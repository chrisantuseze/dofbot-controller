#!/usr/bin/env python3
"""
train_act.py
============
Fine-tunes an ACT (Action-Chunking Transformer) policy on DofBot Pro
demonstration data collected by data_collector.py.

Reads HDF5 episodes directly — no conversion step required.
Outputs checkpoints loadable by lerobot_inference_server.py.

Usage
-----
    # Minimal (sensible defaults, good for proving the pipeline works)
    python train_act.py --dataset_dir dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset

    # Full options
    python train_act.py \\
        --dataset_dir  dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset \\
        --output_dir   runs/act_001 \\
        --chunk_size   20 \\
        --num_steps    50000 \\
        --batch_size   8 \\
        --lr           1e-4 \\
        --save_freq    1000 \\
        --device       cuda

Dependencies
------------
    pip install "lerobot[act]"   # or: pip install lerobot einops
    pip install h5py tensorboard

Checkpoint layout (per save)
-----------------------------
    <output_dir>/checkpoints/step_NNNNN/
        model.pt       ← policy state dict (loadable by inference server)
        config.json    ← ACTConfig fields (reconstruction spec)
        stats.json     ← dataset normalisation stats
"""
import sys
import argparse
import json

import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter

print(str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # robosuite/
sys.path.insert(0, str(Path(__file__).resolve().parent))         # data_capture_wm/

from training.dataset_utils import (
    IMAGE_KEY, STATE_KEY, NUM_JOINTS, ACTION_KEY, compute_stats, infinite_loader, stats_to_json, DofBotDataset
    )


# ── Checkpoint I/O ─────────────────────────────────────────────────────────────

def save_checkpoint(
    ckpt_dir: Path,
    policy: nn.Module,
    config_dict: dict,
    stats: dict,
) -> None:
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    # Model weights
    torch.save(policy.state_dict(), ckpt_dir / "model.pt")

    # ACTConfig fields — used by LocalACTPolicy in the inference server
    with open(ckpt_dir / "config.json", "w") as fh:
        json.dump(config_dict, fh, indent=2)

    # Dataset stats — used by ACTPolicy for normalisation at inference time
    with open(ckpt_dir / "stats.json", "w") as fh:
        json.dump(stats_to_json(stats), fh, indent=2)


# ── Build LeRobot ACT policy ───────────────────────────────────────────────────

def build_policy(
    stats: dict,
    chunk_size: int,
    n_obs_steps: int,
    image_h: int,
    image_w: int,
    device: str,
) -> tuple[nn.Module, dict]:
    """
    Construct an ACTPolicy from LeRobot.

    Returns (policy, config_dict) where config_dict is the plain-dict
    representation of ACTConfig saved alongside each checkpoint.
    """
    try:
        from lerobot.policies.act.configuration_act import ACTConfig
        from lerobot.policies.act.modeling_act import ACTPolicy
        from lerobot.configs.types import FeatureType, PolicyFeature
    except ImportError as exc:
        raise ImportError(
            "LeRobot is not installed.  Run:\n"
            "    pip install 'lerobot[act]'\n"
            "or: pip install lerobot einops"
        ) from exc

    config = ACTConfig(
        input_features={
            IMAGE_KEY: PolicyFeature(type=FeatureType.VISUAL, shape=(3, image_h, image_w)),
            STATE_KEY: PolicyFeature(type=FeatureType.STATE, shape=(NUM_JOINTS,)),
        },
        output_features={
            ACTION_KEY: PolicyFeature(type=FeatureType.ACTION, shape=(NUM_JOINTS,)),
        },
        vision_backbone="resnet18",
        pretrained_backbone_weights="ResNet18_Weights.IMAGENET1K_V1",
        chunk_size=chunk_size,
        n_obs_steps=n_obs_steps,
        n_action_steps=1,
        use_vae=True,
        latent_dim=32,
        dim_model=512,
        n_heads=8,
        dim_feedforward=3200,
        n_encoder_layers=4,
        n_decoder_layers=1,
        temporal_ensemble_coeff=None,
    )

    policy = ACTPolicy(config)
    policy = policy.to(device)

    # Serialisable config dict for checkpoint reconstruction (scalars only)
    config_dict = {
        "chunk_size":                  chunk_size,
        "n_obs_steps":                 n_obs_steps,
        "n_action_steps":              1,
        "image_h":                     image_h,
        "image_w":                     image_w,
        "num_joints":                  NUM_JOINTS,
        "vision_backbone":             config.vision_backbone,
        "pretrained_backbone_weights": config.pretrained_backbone_weights,
        "dim_model":                   config.dim_model,
        "n_heads":                     config.n_heads,
        "dim_feedforward":             config.dim_feedforward,
        "n_encoder_layers":            config.n_encoder_layers,
        "n_decoder_layers":            config.n_decoder_layers,
        "use_vae":                     config.use_vae,
        "latent_dim":                  config.latent_dim,
    }

    return policy, config_dict


# ── Normalisation helper ───────────────────────────────────────────────────────

def normalize_batch(batch: dict, stats: dict, device: str) -> dict:
    """
    Normalise a raw batch from DofBotDataset before passing to ACTPolicy.forward().

    - Squeezes the n_obs_steps=1 time dimension from image and state.
    - Applies (x - mean) / (std + eps) using the dataset stats.
    - Passes action_is_pad through unchanged.
    """
    eps = 1e-8
    out = {}

    # Image: (B, 1, C, H, W) → (B, C, H, W), then normalise channel-wise
    img = batch[IMAGE_KEY].squeeze(1)
    img_mean = stats[IMAGE_KEY]["mean"].to(device)   # (3, 1, 1)
    img_std  = stats[IMAGE_KEY]["std"].to(device)    # (3, 1, 1)
    out[IMAGE_KEY] = (img - img_mean) / (img_std + eps)

    # State: (B, 1, 6) → (B, 6), then normalise per-joint
    state = batch[STATE_KEY].squeeze(1)
    state_mean = stats[STATE_KEY]["mean"].to(device)
    state_std  = stats[STATE_KEY]["std"].to(device)
    out[STATE_KEY] = (state - state_mean) / (state_std + eps)

    # Action: (B, chunk_size, 6), normalise per-joint
    action_mean = stats[ACTION_KEY]["mean"].to(device)
    action_std  = stats[ACTION_KEY]["std"].to(device)
    out[ACTION_KEY] = (batch[ACTION_KEY] - action_mean) / (action_std + eps)

    # Padding mask: pass through as-is
    out["action_is_pad"] = batch["action_is_pad"]

    return out


# ── Training loop ──────────────────────────────────────────────────────────────

def train(args: argparse.Namespace) -> None:
    torch.manual_seed(args.seed)
    device = args.device
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Dataset ───────────────────────────────────────────────────────────────
    dataset = DofBotDataset(
        dataset_dir=Path(args.dataset_dir),
        chunk_size=args.chunk_size,
        n_obs_steps=1,
        image_size=(args.image_size, args.image_size),
    )
    stats = compute_stats(dataset)

    # Persist stats at the run level (also saved per checkpoint)
    with open(output_dir / "stats.json", "w") as fh:
        json.dump(stats_to_json(stats), fh, indent=2)

    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,          # HDF5 + preloaded tensors are main-process safe
        pin_memory=(device != "cpu"),
        drop_last=True,
    )

    # ── Policy ────────────────────────────────────────────────────────────────
    policy, config_dict = build_policy(
        stats=stats,
        chunk_size=args.chunk_size,
        n_obs_steps=1,
        image_h=args.image_size,
        image_w=args.image_size,
        device=device,
    )

    # ── Optimiser ─────────────────────────────────────────────────────────────
    optimizer = torch.optim.Adam(policy.parameters(), lr=args.lr,
                                 weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.num_steps, eta_min=args.lr * 0.01
    )

    # ── TensorBoard writer ────────────────────────────────────────────────────
    writer = SummaryWriter(log_dir=str(output_dir / "tb"))
    print(f"\nTensorBoard: tensorboard --logdir {output_dir / 'tb'}\n")

    # ── Save hyperparams summary ──────────────────────────────────────────────
    hparams = {
        "dataset_dir":  args.dataset_dir,
        "num_episodes": len(dataset.episodes),
        "total_frames": sum(ep["length"] for ep in dataset.episodes),
        "num_samples":  len(dataset),
        "batch_size":   args.batch_size,
        "chunk_size":   args.chunk_size,
        "num_steps":    args.num_steps,
        "lr":           args.lr,
        "device":       device,
    }
    with open(output_dir / "hparams.json", "w") as fh:
        json.dump(hparams, fh, indent=2)

    # ── Training ──────────────────────────────────────────────────────────────
    policy.train()
    data_iter  = infinite_loader(loader)
    step       = 0
    t_start    = time.time()

    print(f"Training for {args.num_steps} gradient steps "
          f"(batch={args.batch_size}, chunk={args.chunk_size}, "
          f"device={device})…")
    print("Step     Loss     LR       Elapsed")
    print("------  -------  -------  --------")

    while step < args.num_steps:
        batch = next(data_iter)

        # ── Forward pass ──────────────────────────────────────────────────────
        optimizer.zero_grad()

        # Move to device and normalise
        batch = {k: v.to(device) for k, v in batch.items()}
        batch = normalize_batch(batch, stats, device)

        try:
            # ACTPolicy.forward returns (loss_tensor, loss_dict)
            loss, loss_dict = policy.forward(batch)
            loss_info = {k: v for k, v in loss_dict.items()}
        except Exception as exc:
            raise RuntimeError(
                f"policy.forward() failed at step {step}.\n"
                f"Batch keys: {list(batch.keys())}\n"
                f"Batch shapes: {[(k, v.shape) for k, v in batch.items() if hasattr(v, 'shape')]}\n"
                f"Original error: {exc}"
            ) from exc

        # ── Backward + update ─────────────────────────────────────────────────
        loss.backward()
        nn.utils.clip_grad_norm_(policy.parameters(), max_norm=10.0)
        optimizer.step()
        scheduler.step()

        step += 1
        loss_val = loss.item()

        # ── Logging ───────────────────────────────────────────────────────────
        writer.add_scalar("train/loss", loss_val, step)
        for k, v in loss_info.items():
            if k != "loss":
                writer.add_scalar(f"train/{k}", v, step)
        writer.add_scalar("train/lr", scheduler.get_last_lr()[0], step)

        if step % args.print_freq == 0 or step == 1:
            elapsed = time.time() - t_start
            lr_now  = scheduler.get_last_lr()[0]
            suffix  = "  [" + "  ".join(f"{k}={v:.4f}" for k, v in loss_info.items()
                                         if k != "loss") + "]" if loss_info else ""
            print(f"{step:6d}  {loss_val:.5f}  {lr_now:.2e}  "
                  f"{elapsed:6.0f}s{suffix}")

        # ── Checkpoint ────────────────────────────────────────────────────────
        if step % args.save_freq == 0 or step == args.num_steps:
            ckpt_dir = output_dir / "checkpoints" / f"step_{step:06d}"
            save_checkpoint(ckpt_dir, policy, config_dict, stats)
            print(f"  → checkpoint saved: {ckpt_dir}")

    writer.close()
    print(f"\nTraining complete.  Final checkpoint: "
          f"{output_dir / 'checkpoints' / f'step_{step:06d}'}")
    print(f"\nTo run inference:")
    print(f"  python lerobot_inference_server.py \\")
    print(f"    --policy_type act \\")
    print(f"    --checkpoint_path {output_dir / 'checkpoints' / f'step_{step:06d}'} \\")
    print(f"    --inference_hz 5")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune ACT on DofBot Pro demonstrations.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Data
    parser.add_argument(
        "--dataset_dir",
        required=True,
        help="Directory containing episode_XXXXXX.hdf5 files",
    )
    parser.add_argument(
        "--output_dir",
        default="runs/act_001",
        help="Directory for TensorBoard logs and checkpoints",
    )

    # Model
    parser.add_argument(
        "--chunk_size", default=10, type=int,
        help="Number of future actions to predict per inference step. "
             "At 5 fps, chunk_size=10 → 2-second action horizon.",
    )
    parser.add_argument(
        "--image_size", default=224, type=int,
        help="Square image side length (must match recording resolution)",
    )

    # Training
    parser.add_argument(
        "--num_steps", default=50_000, type=int,
        help="Total gradient steps.  Use 5000 for a quick pipeline test "
             "with 2 episodes (will overfit, that's expected).",
    )
    parser.add_argument("--batch_size", default=8,    type=int)
    parser.add_argument("--lr",         default=1e-4, type=float)
    parser.add_argument(
        "--save_freq", default=2000, type=int,
        help="Save a checkpoint every N gradient steps.",
    )
    parser.add_argument(
        "--print_freq", default=200, type=int,
        help="Print training progress every N steps (loss, elapsed time, etc.)",
    )

    # System
    parser.add_argument(
        "--device", default="cuda" if torch.cuda.is_available() else "cpu",
        help="Torch device: cpu | cuda | cuda:0 | mps",
    )
    parser.add_argument("--seed", default=42, type=int)

    return parser.parse_args()


if __name__ == "__main__":
    train(parse_args())
