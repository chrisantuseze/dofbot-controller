#!/usr/bin/env python3
"""
train_pi0.py
============
Fine-tunes a pi0 (Physical Intelligence π₀) policy on DofBot Pro
demonstration data.

Pi0 uses PaliGemma (3B VLM) + a flow-matching action expert. Training from
scratch is not practical — always fine-tune from the pretrained "lerobot/pi0"
HuggingFace checkpoint (or a local copy of it).

Because pi0 uses LeRobot's dataset infrastructure for tokenisation,
you must first convert your HDF5 episodes to the LeRobot v2 format:

    python training/convert_to_lerobot.py \\
        --input_dir  dofbot_pro_ws/src/dofbot_policy_bridge/dofbot_dataset \\
        --output_dir runs/lerobot_dataset

Then fine-tune:

    python training/train_pi0.py \\
        --lerobot_dir  runs/lerobot_dataset \\
        --output_dir   runs/pi0_001 \\
        --num_steps    10000 \\
        --batch_size   4 \\
        --device       cuda

Hardware
--------
Pi0 is a 3B-parameter model. Minimum recommended:
  - GPU with ≥ 16 GB VRAM for bfloat16 / float32 training
  - Set --train_expert_only (default) to freeze the VLM and only train the
    action expert + projections (needs ~6–8 GB VRAM)

Checkpoint layout (per save)
-----------------------------
    <output_dir>/checkpoints/step_NNNNNN/
        model.safetensors  ← policy weights
        config.json        ← PI0Config with input/output features
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


def save_checkpoint(
    ckpt_dir: Path,
    policy: nn.Module,
    stats: dict,
) -> None:
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    # Save model.safetensors + config.json via LeRobot's built-in method
    policy._save_pretrained(ckpt_dir)

    # Save dataset stats for inference-time unnormalisation
    with open(ckpt_dir / "stats.json", "w") as fh:
        json.dump(_stats_to_json(stats), fh, indent=2)

    print(f"  → checkpoint saved: {ckpt_dir}")


# ── Build policy ───────────────────────────────────────────────────────────────

def build_policy(
    pretrained: str,
    dataset_meta,
    chunk_size: int,
    train_expert_only: bool,
    dtype: str,
    device: str,
) -> nn.Module:
    """
    Load the pretrained pi0 checkpoint and adapt its config for this dataset.

    Parameters
    ----------
    pretrained:
        HuggingFace repo id (e.g. "lerobot/pi0") or local path to a pi0
        checkpoint directory.
    dataset_meta:
        LeRobotDatasetMetadata instance with .features and .stats.
    chunk_size:
        Number of future action steps to predict (action horizon).
    train_expert_only:
        If True (default), freeze the entire VLM (PaliGemma) and only train
        the action expert + projection heads. Requires ~6–8 GB VRAM.
        If False, all parameters are unfrozen (needs ~20+ GB VRAM).
    dtype:
        "float32" or "bfloat16".
    device:
        PyTorch device string ("cpu", "cuda", "cuda:0", "mps").
    """
    from lerobot.policies.pi0.modeling_pi0 import PI0Policy
    from lerobot.policies.pi0.configuration_pi0 import PI0Config
    from lerobot.datasets.utils import dataset_to_policy_features

    # Convert dataset feature spec → PolicyFeature dicts
    policy_features = dataset_to_policy_features(dataset_meta.features)
    input_features  = {k: f for k, f in policy_features.items() if k != "action"}
    output_features = {"action": policy_features["action"]}

    # Build a new PI0Config adapted to this dataset
    config = PI0Config(
        input_features=input_features,
        output_features=output_features,
        chunk_size=chunk_size,
        n_action_steps=chunk_size,
        dtype=dtype,
        device=device,
        train_expert_only=train_expert_only,
    )

    print(f"Loading pretrained pi0 from: {pretrained}")
    print("(This may download ~5 GB from HuggingFace the first time.)")
    policy = PI0Policy.from_pretrained(pretrained, config=config)
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
    repo_id     = lerobot_dir.name   # folder name used as the local repo_id

    print(f"Loading LeRobot dataset from: {lerobot_dir}")
    ds_meta = LeRobotDatasetMetadata(repo_id=repo_id, root=lerobot_dir)

    # Pi0 predicts a chunk_size-length action sequence;
    # pass delta_timestamps so the dataloader returns that many future actions.
    delta_timestamps = {
        "action": [i / ds_meta.fps for i in range(args.chunk_size)],
    }

    dataset = LeRobotDataset(
        repo_id=repo_id,
        root=lerobot_dir,
        delta_timestamps=delta_timestamps,
    )

    stats = ds_meta.stats  # dict[str, dict[str, Tensor]]

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
        dtype=args.dtype,
        device=device,
    )

    # ── Preprocessor ─────────────────────────────────────────────────────────
    # Handles tokenisation of the per-batch task strings and normalisation.
    # Safe to call on an already-batched dict from the dataloader — the
    # AddBatchDimensionProcessorStep checks dimensions and skips if already batched.
    from lerobot.policies.pi0.processor_pi0 import make_pi0_pre_post_processors

    preprocessor, _ = make_pi0_pre_post_processors(
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
        "lerobot_dir":      args.lerobot_dir,
        "pretrained":       args.pretrained,
        "num_episodes":     ds_meta.total_episodes,
        "total_frames":     ds_meta.total_frames,
        "batch_size":       args.batch_size,
        "chunk_size":       args.chunk_size,
        "num_steps":        args.num_steps,
        "lr":               lr,
        "dtype":            args.dtype,
        "train_expert_only": args.train_expert_only,
        "device":           device,
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
    print(f"    --policy_type pi_0 \\")
    print(f"    --checkpoint_path {final_ckpt} \\")
    print(f"    --task_prompt 'pick and place object' \\")
    print(f"    --inference_hz 5")


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune pi0 on DofBot Pro demonstrations (LeRobot v2 dataset required).",
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
        default="runs/pi0_001",
        help="Directory for TensorBoard logs and checkpoints",
    )

    # ── Pretrained base ───────────────────────────────────────────────────────
    parser.add_argument(
        "--pretrained",
        default="lerobot/pi0",
        help=(
            "HuggingFace repo id or local path for the pretrained pi0 checkpoint. "
            "Downloads ~5 GB from HuggingFace the first time."
        ),
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    parser.add_argument(
        "--chunk_size",
        default=50,
        type=int,
        help=(
            "Action horizon: number of future steps to predict. "
            "Pi0 default is 50. Use a smaller value (e.g. 20) if GPU memory is tight."
        ),
    )
    parser.add_argument(
        "--train_expert_only",
        action="store_true",
        default=True,
        help=(
            "Freeze the PaliGemma VLM backbone and only train the action expert + "
            "projection heads (~6–8 GB VRAM). Recommended for most fine-tuning."
        ),
    )
    parser.add_argument(
        "--no_train_expert_only",
        dest="train_expert_only",
        action="store_false",
        help="Unfreeze all parameters (full fine-tune). Requires ~20+ GB VRAM.",
    )
    parser.add_argument(
        "--dtype",
        default="float32",
        choices=["float32", "bfloat16"],
        help="Model dtype. Use bfloat16 to save memory on CUDA.",
    )

    # ── Training ──────────────────────────────────────────────────────────────
    parser.add_argument(
        "--num_steps",
        default=10_000,
        type=int,
        help=(
            "Total gradient steps. "
            "10 000 is a reasonable starting point for ~20 episodes; "
            "increase to 30 000+ for 50+ episodes."
        ),
    )
    parser.add_argument("--batch_size",  default=4,    type=int)
    parser.add_argument(
        "--lr",
        default=None,
        type=float,
        help=(
            "Learning rate. Defaults to the pi0 preset (2.5e-5) if not set. "
            "A lower value (e.g. 1e-5) is safer when fine-tuning expert-only."
        ),
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

    # Auto-detect MPS (Apple Silicon)
    if args.device == "cuda" and not torch.cuda.is_available():
        try:
            if torch.backends.mps.is_available():
                args.device = "mps"
                print("[train_pi0] CUDA not found — using MPS (Apple Silicon).")
            else:
                args.device = "cpu"
                print("[train_pi0] No GPU found — falling back to CPU (will be slow).")
        except AttributeError:
            args.device = "cpu"

    train(args)
