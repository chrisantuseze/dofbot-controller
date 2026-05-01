#!/usr/bin/env python3
"""
train_smolvla.py
================
Fine-tunes a SmolVLA (SmolVLM2-500M-based VLA) policy on DofBot Pro
demonstration data.

SmolVLA is a compact (~450 M parameter) vision-language-action model designed
to run on consumer GPUs (≤ 7 GB VRAM with train_expert_only=True) while
matching larger VLA performance.

Like pi0, SmolVLA requires the dataset in LeRobot v2 format.  Convert first:

    python training/convert_to_lerobot.py \\
        --input_dir  dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset \\
        --output_dir runs/lerobot_dataset

Then fine-tune:

    python training/train_smolvla.py \\
        --lerobot_dir  runs/lerobot_dataset \\
        --output_dir   runs/smolvla_001 \\
        --num_steps    10000 \\
        --batch_size   8 \\
        --device       cuda

Hardware
--------
  - Default (train_expert_only): VLM frozen, only action expert + projections
    trained. Requires ~2–4 GB VRAM. batch_size=8 is comfortable on 7 GB.
  - Full fine-tune (--no_train_expert_only): ~6–8 GB VRAM.

Checkpoint layout (per save)
-----------------------------
    <output_dir>/checkpoints/step_NNNNNN/
        model.safetensors  ← policy weights
        config.json        ← SmolVLAConfig with input/output features
        stats.json         ← dataset normalisation stats (for inference)
"""

import sys
import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))


# ── Checkpoint I/O ─────────────────────────────────────────────────────────────

def _stats_to_json(stats: dict) -> dict:
    """Convert a stats dict (with Tensor values) to a JSON-serialisable dict."""
    out = {}
    for feat, d in stats.items():
        out[feat] = {
            k: v.tolist() if hasattr(v, "tolist") else v
            for k, v in d.items()
        }
    return out


def save_checkpoint(ckpt_dir: Path, policy: nn.Module, stats: dict) -> None:
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    policy._save_pretrained(ckpt_dir)
    with open(ckpt_dir / "stats.json", "w") as fh:
        json.dump(_stats_to_json(stats), fh, indent=2)
    print(f"  → checkpoint saved: {ckpt_dir}")


# ── Build policy ───────────────────────────────────────────────────────────────

def build_policy(
    pretrained: str,
    dataset_meta,
    chunk_size: int,
    train_expert_only: bool,
    device: str,
) -> nn.Module:
    """
    Load the pretrained SmolVLA checkpoint and adapt its config for this dataset.

    Parameters
    ----------
    pretrained:
        HuggingFace repo id (e.g. "lerobot/smolvla_base") or local path.
    dataset_meta:
        LeRobotDatasetMetadata instance with .features and .stats.
    chunk_size:
        Number of future action steps to predict (action horizon).
    train_expert_only:
        Freeze the VLM backbone; train only the action expert + state/action
        projections (~2–4 GB VRAM). Recommended for 7 GB GPU.
    device:
        PyTorch device string.
    """
    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
    from lerobot.datasets.utils import dataset_to_policy_features

    policy_features = dataset_to_policy_features(dataset_meta.features)
    input_features  = {k: f for k, f in policy_features.items() if k != "action"}
    output_features = {"action": policy_features["action"]}

    config = SmolVLAConfig(
        input_features=input_features,
        output_features=output_features,
        chunk_size=chunk_size,
        n_action_steps=chunk_size,
        train_expert_only=train_expert_only,
        freeze_vision_encoder=train_expert_only,
        device=device,
    )

    print(f"Loading pretrained SmolVLA from: {pretrained}")
    print("(Downloads ~1 GB from HuggingFace the first time.)")
    policy = SmolVLAPolicy.from_pretrained(pretrained, config=config)
    policy = policy.to(device)
    policy.train()
    return policy


# ── Training loop ──────────────────────────────────────────────────────────────

def train(args: argparse.Namespace) -> None:
    torch.manual_seed(args.seed)
    device     = args.device
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Dataset ───────────────────────────────────────────────────────────────
    from lerobot.datasets.lerobot_dataset import LeRobotDataset, LeRobotDatasetMetadata

    lerobot_dir = Path(args.lerobot_dir)
    repo_id     = lerobot_dir.name

    print(f"Loading LeRobot dataset from: {lerobot_dir}")
    ds_meta = LeRobotDatasetMetadata(repo_id=repo_id, root=lerobot_dir)

    delta_timestamps = {
        "action": [i / ds_meta.fps for i in range(args.chunk_size)],
    }

    dataset = LeRobotDataset(
        repo_id=repo_id,
        root=lerobot_dir,
        delta_timestamps=delta_timestamps,
    )

    stats = ds_meta.stats

    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=(device != "cpu"),
        drop_last=True,
    )

    # ── Policy ────────────────────────────────────────────────────────────────
    policy = build_policy(
        pretrained=args.pretrained,
        dataset_meta=ds_meta,
        chunk_size=args.chunk_size,
        train_expert_only=args.train_expert_only,
        device=device,
    )

    # ── Preprocessor ─────────────────────────────────────────────────────────
    from lerobot.policies.smolvla.processor_smolvla import make_smolvla_pre_post_processors

    preprocessor, _ = make_smolvla_pre_post_processors(
        config=policy.config,
        dataset_stats=stats,
    )

    # ── Optimiser ─────────────────────────────────────────────────────────────
    optim_preset = policy.config.get_optimizer_preset()
    lr = args.lr if args.lr is not None else optim_preset.lr

    optimizer = torch.optim.AdamW(
        policy.parameters(),
        lr=lr,
        betas=optim_preset.betas,
        eps=optim_preset.eps,
        weight_decay=optim_preset.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=args.num_steps,
        eta_min=lr * 0.01,
    )

    grad_clip = policy.config.optimizer_grad_clip_norm

    # ── TensorBoard ───────────────────────────────────────────────────────────
    writer = SummaryWriter(log_dir=str(output_dir / "tb"))
    print(f"\nTensorBoard: tensorboard --logdir {output_dir / 'tb'}\n")

    # ── Hparams summary ───────────────────────────────────────────────────────
    hparams = {
        "lerobot_dir":       args.lerobot_dir,
        "pretrained":        args.pretrained,
        "num_episodes":      ds_meta.total_episodes,
        "total_frames":      ds_meta.total_frames,
        "batch_size":        args.batch_size,
        "chunk_size":        args.chunk_size,
        "num_steps":         args.num_steps,
        "lr":                lr,
        "train_expert_only": args.train_expert_only,
        "device":            device,
    }
    with open(output_dir / "hparams.json", "w") as fh:
        json.dump(hparams, fh, indent=2)

    # ── Training ──────────────────────────────────────────────────────────────
    def _infinite_loader(dl):
        while True:
            yield from dl

    data_iter = _infinite_loader(loader)
    step      = 0
    t_start   = time.time()

    mode = ("train_expert_only (VLM frozen)" if args.train_expert_only
            else "full fine-tune (all params)")
    print(f"Training for {args.num_steps} gradient steps  "
          f"(batch={args.batch_size}, chunk={args.chunk_size}, mode={mode})…")
    print("Step     Loss     LR       Elapsed")
    print("------  -------  -------  --------")

    while step < args.num_steps:
        batch = next(data_iter)

        # Tokenise task strings + normalise state/action ──────────────────────
        batch = preprocessor(batch)

        # Forward ─────────────────────────────────────────────────────────────
        optimizer.zero_grad()
        policy.train()

        try:
            loss, loss_dict = policy.forward(batch)
        except Exception as exc:
            raise RuntimeError(
                f"policy.forward() failed at step {step}.\n"
                f"Batch keys: {list(batch.keys())}\n"
                f"Original error: {exc}"
            ) from exc

        # Backward + update ────────────────────────────────────────────────────
        loss.backward()
        nn.utils.clip_grad_norm_(policy.parameters(), max_norm=grad_clip)
        optimizer.step()
        scheduler.step()

        step    += 1
        loss_val = loss.item()

        # Logging ──────────────────────────────────────────────────────────────
        writer.add_scalar("train/loss", loss_val, step)
        for k, v in loss_dict.items():
            if k != "loss":
                writer.add_scalar(f"train/{k}", v if isinstance(v, float) else v.item(), step)
        writer.add_scalar("train/lr", scheduler.get_last_lr()[0], step)

        if step % args.print_freq == 0 or step == 1:
            elapsed = time.time() - t_start
            lr_now  = scheduler.get_last_lr()[0]
            print(f"{step:6d}  {loss_val:.5f}  {lr_now:.2e}  {elapsed:6.0f}s")

        # Checkpoint ───────────────────────────────────────────────────────────
        if step % args.save_freq == 0 or step == args.num_steps:
            ckpt_dir = output_dir / "checkpoints" / f"step_{step:06d}"
            save_checkpoint(ckpt_dir, policy, stats)

    writer.close()
    final_ckpt = output_dir / "checkpoints" / f"step_{step:06d}"
    print(f"\nTraining complete.  Final checkpoint: {final_ckpt}")
    print(f"\nTo run inference:")
    print(f"  python inference/lerobot_inference_server.py \\")
    print(f"    --policy_type     smolvla \\")
    print(f"    --checkpoint_path {final_ckpt} \\")
    print(f"    --task_prompt     'pick and place object' \\")
    print(f"    --inference_hz    5")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune SmolVLA on DofBot Pro demonstrations (LeRobot v2 dataset required).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ── Data ──────────────────────────────────────────────────────────────────
    parser.add_argument(
        "--lerobot_dir",
        required=True,
        help="Path to the LeRobot v2 dataset directory produced by convert_to_lerobot.py",
    )
    parser.add_argument(
        "--output_dir",
        default="runs/smolvla_001",
        help="Directory for TensorBoard logs and checkpoints",
    )

    # ── Pretrained base ───────────────────────────────────────────────────────
    parser.add_argument(
        "--pretrained",
        default="lerobot/smolvla_base",
        help=(
            "HuggingFace repo id or local path for the pretrained SmolVLA checkpoint. "
            "Downloads ~1 GB from HuggingFace the first time."
        ),
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    parser.add_argument(
        "--chunk_size",
        default=10,
        type=int,
        help=(
            "Action horizon: number of future steps to predict. "
            "At 5 fps, chunk_size=10 → 2-second horizon. "
            "SmolVLA default is 50 but smaller values use less memory."
        ),
    )
    parser.add_argument(
        "--train_expert_only",
        action="store_true",
        default=True,
        help=(
            "Freeze the VLM backbone and only train the action expert + "
            "state/action projections. ~2–4 GB VRAM. Recommended for 7 GB GPU."
        ),
    )
    parser.add_argument(
        "--no_train_expert_only",
        dest="train_expert_only",
        action="store_false",
        help="Unfreeze all parameters (full fine-tune). ~6–8 GB VRAM.",
    )

    # ── Training ──────────────────────────────────────────────────────────────
    parser.add_argument(
        "--num_steps",
        default=10_000,
        type=int,
        help=(
            "Total gradient steps. "
            "10 000 is a good starting point for ~20 episodes; "
            "increase to 30 000+ for 50+ episodes."
        ),
    )
    parser.add_argument("--batch_size",  default=8,    type=int,
                        help="Batch size. 8 fits comfortably in 7 GB with train_expert_only.")
    parser.add_argument(
        "--lr",
        default=None,
        type=float,
        help="Learning rate. Defaults to the SmolVLA preset (1e-4) if not set.",
    )
    parser.add_argument(
        "--save_freq",
        default=2000,
        type=int,
        help="Save a checkpoint every N gradient steps.",
    )
    parser.add_argument(
        "--print_freq",
        default=200,
        type=int,
        help="Print training progress every N steps.",
    )
    parser.add_argument("--seed",   default=42, type=int)
    parser.add_argument("--device", default="cuda", type=str,
                        help="cpu | cuda | cuda:0 | mps")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        try:
            if torch.backends.mps.is_available():
                args.device = "mps"
                print("[train_smolvla] CUDA not found — using MPS (Apple Silicon).")
            else:
                args.device = "cpu"
                print("[train_smolvla] No GPU found — falling back to CPU (will be slow).")
        except AttributeError:
            args.device = "cpu"

    train(args)
