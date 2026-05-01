#!/usr/bin/env python3

from pathlib import Path
import json
import numpy as np

import torch
from lerobot.policies.act.configuration_act import ACTConfig
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.configs.types import FeatureType, PolicyFeature

# from lerobot.common.policies.diffusion.modeling_diffusion import DiffusionPolicy
# from lerobot.common.utils.utils import init_hydra_config

import constants

# ── Policy classes ─────────────────────────────────────────────────────────────

class MockPolicy:
    """
    No ML required. Cycles through safe waypoints (near home, ±10° per joint)
    to confirm the full Jetson ↔ lab ↔ servo pipeline is wired correctly.

    Run with --inference_hz 0.2 --move_time_ms 2000 so movements are slow.
    """
    _WAYPOINTS = [
        [90.0,  90.0,  90.0,  0.0,  90.0,  30.0],   # home
        [100.0, 90.0,  90.0,  0.0,  90.0,  30.0],   # Arm1 +10°
        [90.0, 100.0,  90.0,  0.0,  90.0,  30.0],   # Arm2 +10°
        [90.0,  90.0, 100.0,  0.0,  90.0,  30.0],   # Arm3 +10°
        [90.0,  90.0,  90.0, 10.0,  90.0,  30.0],   # Arm4 +10°
        [90.0,  90.0,  90.0,  0.0, 100.0,  30.0],   # Arm5 +10°
        [90.0,  90.0,  90.0,  0.0,  90.0, 100.0],   # gripper close
        [90.0,  90.0,  90.0,  0.0,  90.0,  30.0],   # home (gripper open)
        [90.0,  140.0,  90.0,  0.0,  90.0,  30.0],   # 
    ]

    def __init__(self):
        self._step = 0
        print(f"[MockPolicy] Loaded — {len(self._WAYPOINTS)} waypoints")

    def predict(self, obs: dict) -> np.ndarray:
        deg = self._WAYPOINTS[self._step % len(self._WAYPOINTS)]
        print(f"[MockPolicy] Waypoint {self._step % len(self._WAYPOINTS)}: {deg} deg")
        self._step += 1
        # Convert to radians (same convention as /joint_states)
        rad = [(d - 90.0) * constants.DEG2RAD for d in deg[:5]]
        grip_state = float(np.interp(deg[5],
                                     [constants.GRIPPER_MIN_DEG, constants.GRIPPER_MAX_DEG],
                                     [constants.GRIPPER_STATE_MIN_DEG, constants.GRIPPER_STATE_MAX_DEG]))
        rad.append((grip_state - 90.0) * constants.DEG2RAD)
        return np.array(rad, dtype=np.float32)

class LocalACTPolicy:
    """
    Fine-tuned ACT checkpoint produced by train_act.py.

    Checkpoint layout (output of train_act.py):
        <checkpoint_dir>/model.pt      ← policy state dict
        <checkpoint_dir>/config.json   ← scalar ACT hyper-parameters
        <checkpoint_dir>/stats.json    ← dataset normalisation stats
    """
    def __init__(self, checkpoint_path: str, device: str = "cpu"):
        ckpt_dir = Path(checkpoint_path)

        with open(ckpt_dir / "config.json") as fh:
            cfg = json.load(fh)

        with open(ckpt_dir / "stats.json") as fh:
            stats_raw = json.load(fh)
        self.stats = {
            feat: {k: torch.tensor(v) for k, v in vals.items()}
            for feat, vals in stats_raw.items()
        }

        image_key = "observation.images.top"
        state_key = "observation.state"
        action_key = "action"
        num_joints = cfg.get("num_joints", constants.NUM_JOINTS)
        image_h    = cfg.get("image_h", 224)
        image_w    = cfg.get("image_w", 224)

        config = ACTConfig(
            input_features={
                image_key: PolicyFeature(type=FeatureType.VISUAL, shape=(3, image_h, image_w)),
                state_key: PolicyFeature(type=FeatureType.STATE, shape=(num_joints,)),
            },
            output_features={
                action_key: PolicyFeature(type=FeatureType.ACTION, shape=(num_joints,)),
            },
            chunk_size=cfg["chunk_size"],
            n_obs_steps=cfg["n_obs_steps"],
            n_action_steps=cfg["n_action_steps"],
            vision_backbone=cfg.get("vision_backbone", "resnet18"),
            pretrained_backbone_weights=cfg.get("pretrained_backbone_weights",
                                                 "ResNet18_Weights.IMAGENET1K_V1"),
            dim_model=cfg.get("dim_model", 512),
            n_heads=cfg.get("n_heads", 8),
            dim_feedforward=cfg.get("dim_feedforward", 3200),
            n_encoder_layers=cfg.get("n_encoder_layers", 4),
            n_decoder_layers=cfg.get("n_decoder_layers", 1),
            use_vae=cfg.get("use_vae", True),
            latent_dim=cfg.get("latent_dim", 32),
        )
        self.image_key  = image_key
        self.state_key  = state_key
        self.action_key = action_key

        self.policy = ACTPolicy(config)
        self.policy.load_state_dict(
            torch.load(ckpt_dir / "model.pt", map_location=device,
                       weights_only=True)
        )
        self.policy = self.policy.to(device)
        self.policy.eval()
        self.device = device
        print(f"[ACTPolicy] Loaded from {checkpoint_path}")

    def predict(self, obs: dict) -> np.ndarray:
        eps = 1e-8
        device = self.device

        # obs["image"] is (C, H, W) float32 [0,1]
        image = torch.from_numpy(obs["image"]).float().to(device)  # (C, H, W)
        state = torch.from_numpy(obs["state"]).float().to(device)  # (constants.NUM_JOINTS,)

        # Normalise image channel-wise
        img_mean = self.stats[self.image_key]["mean"].to(device)   # (3, 1, 1)
        img_std  = self.stats[self.image_key]["std"].to(device)    # (3, 1, 1)
        image_norm = (image - img_mean) / (img_std + eps)

        # Normalise state per-joint
        st_mean = self.stats[self.state_key]["mean"].to(device)
        st_std  = self.stats[self.state_key]["std"].to(device)
        state_norm = (state - st_mean) / (st_std + eps)

        # Add batch dimension: policy expects (B, C, H, W) and (B, state_dim)
        batch = {
            self.image_key: image_norm.unsqueeze(0),    # (1, C, H, W)
            self.state_key: state_norm.unsqueeze(0),    # (1, constants.NUM_JOINTS)
        }
        with torch.no_grad():
            action_norm = self.policy.select_action(batch)   # (1, constants.NUM_JOINTS) or (constants.NUM_JOINTS,)

        # Unnormalise action
        act_mean = self.stats[self.action_key]["mean"].to(device)
        act_std  = self.stats[self.action_key]["std"].to(device)
        action = action_norm * (act_std + eps) + act_mean

        a = action.cpu().numpy()
        if a.ndim == 3:
            a = a[0, 0]
        elif a.ndim == 2:
            a = a[0]
        return a.flatten()[:constants.NUM_JOINTS].astype(np.float32)


class LocalDiffusionPolicy:
    """Fine-tuned Diffusion Policy checkpoint stored on disk."""
    def __init__(self, checkpoint_path: str, device: str = "cpu"):
        cfg = init_hydra_config(checkpoint_path)
        self.policy = DiffusionPolicy(cfg.policy)
        self.policy.load_state_dict(
            torch.load(f"{checkpoint_path}/model.pt", map_location=device)
        )
        self.policy.eval()
        self.device = device
        print(f"[DiffusionPolicy] Loaded from {checkpoint_path}")

    def predict(self, obs: dict) -> np.ndarray:
        image = torch.from_numpy(obs["image"]).float().unsqueeze(0).to(self.device)
        state = torch.from_numpy(obs["state"]).float().unsqueeze(0).to(self.device)
        with torch.no_grad():
            action = self.policy.select_action({
                "observation.image": image,
                "observation.state": state,
            })
        a = action.cpu().numpy()
        if a.ndim == 3:
            a = a[0, 0]
        elif a.ndim == 2:
            a = a[0]
        return a.flatten()[:constants.NUM_JOINTS].astype(np.float32)


class LocalPi0Policy:
    """
    Fine-tuned pi0 checkpoint produced by training/train_pi0.py.

    Pi0 is a language-conditioned flow-matching policy built on PaliGemma (3B VLM).
    A task prompt is required at inference time to condition the model.

    Checkpoint layout (output of train_pi0.py):
        <checkpoint_dir>/model.safetensors  ← policy weights
        <checkpoint_dir>/config.json        ← PI0Config (with input/output features)
        <checkpoint_dir>/stats.json         ← dataset normalisation stats

    Parameters
    ----------
    checkpoint_path:
        Path to the checkpoint directory saved by train_pi0.py.
    task_prompt:
        Natural-language task description, e.g. "pick and place yellow cube to side area".
        This conditions the VLM backbone.
    device:
        PyTorch device string ("cpu", "cuda", "cuda:0", "mps").
    """

    def __init__(self, checkpoint_path: str, task_prompt: str, device: str = "cpu"):
        from lerobot.policies.pi0.modeling_pi0 import PI0Policy
        from lerobot.policies.pi0.processor_pi0 import make_pi0_pre_post_processors

        ckpt_dir = Path(checkpoint_path)

        # Load dataset normalisation stats saved alongside the checkpoint
        with open(ckpt_dir / "stats.json") as fh:
            stats_raw = json.load(fh)
        stats = {
            feat: {k: torch.tensor(v) for k, v in vals.items()}
            for feat, vals in stats_raw.items()
        }

        # Load policy weights + config (PI0Policy.from_pretrained handles local dirs)
        self.policy = PI0Policy.from_pretrained(str(ckpt_dir))
        self.policy = self.policy.to(device)
        self.policy.eval()
        self.policy.reset()

        # Build the preprocessor pipeline:
        #   RenameObservations → AddBatchDim → Pi0NewLine → Tokeniser → Device → Normalise
        # The TokenizerProcessorStep downloads the paligemma tokeniser on first use
        # (~5 MB, cached in ~/.cache/huggingface/).
        self.preprocessor, self.postprocessor = make_pi0_pre_post_processors(
            config=self.policy.config,
            dataset_stats=stats,
        )

        self.task_prompt = task_prompt
        self.stats       = stats
        self.device      = device
        self.image_key   = "observation.images.top"
        self.state_key   = "observation.state"
        self.action_key  = "action"
        print(f"[Pi0Policy] Loaded from {checkpoint_path}")
        print(f"[Pi0Policy] Task prompt: '{task_prompt}'")

    def predict(self, obs: dict) -> np.ndarray:
        """
        Run one inference step.

        Parameters
        ----------
        obs["image"]:  (C, H, W) float32 in [0, 1], RGB channel-first
        obs["state"]:  (NUM_JOINTS,) float32 joint angles in radians

        Returns
        -------
        np.ndarray, shape (NUM_JOINTS,), joint angles in radians
        """
        device = self.device

        # Build a single-sample observation dict using the LeRobot key convention
        image = torch.from_numpy(obs["image"]).float()  # (C, H, W)
        state = torch.from_numpy(obs["state"]).float()  # (NUM_JOINTS,)

        # The preprocessor's AddBatchDimensionProcessorStep will add the batch
        # dimension because images are 3D and state is 1D at this point.
        single_obs = {
            self.image_key: image,
            self.state_key: state,
            "task": self.task_prompt,  # string → tokenised by TokenizerProcessorStep
        }

        # Apply full preprocessor: tokenise + normalise + move to device
        batch = self.preprocessor(single_obs)

        with torch.no_grad():
            # Returns (1, NUM_JOINTS) tensor in normalised action space
            action_norm = self.policy.select_action(batch)

        # Unnormalise action using ACTION mean/std from dataset stats
        eps = 1e-8
        act_mean = self.stats[self.action_key]["mean"].to("cpu")
        act_std  = self.stats[self.action_key]["std"].to("cpu")
        action   = action_norm.cpu() * (act_std + eps) + act_mean

        a = action.numpy()
        if a.ndim == 2:
            a = a[0]
        return a.flatten()[:constants.NUM_JOINTS].astype(np.float32)


class LocalSmolVLAPolicy:
    """
    Fine-tuned SmolVLA checkpoint produced by training/train_smolvla.py.

    SmolVLA is a compact (~450 M parameter) VLA built on SmolVLM2-500M.
    It requires only ~0.9 GB VRAM at inference and ~2–4 GB for fine-tuning,
    making it suitable for 7 GB consumer GPUs.

    Checkpoint layout (output of train_smolvla.py):
        <checkpoint_dir>/model.safetensors  ← policy weights
        <checkpoint_dir>/config.json        ← SmolVLAConfig
        <checkpoint_dir>/stats.json         ← dataset normalisation stats

    Parameters
    ----------
    checkpoint_path:
        Path to the checkpoint directory saved by train_smolvla.py.
    task_prompt:
        Natural-language task description, e.g. "pick and place yellow cube to side area".
    device:
        PyTorch device string ("cpu", "cuda", "cuda:0", "mps").
    """

    def __init__(self, checkpoint_path: str, task_prompt: str, device: str = "cpu"):
        from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
        from lerobot.policies.smolvla.processor_smolvla import make_smolvla_pre_post_processors

        ckpt_dir = Path(checkpoint_path)

        with open(ckpt_dir / "stats.json") as fh:
            stats_raw = json.load(fh)
        stats = {
            feat: {k: torch.tensor(v) for k, v in vals.items()}
            for feat, vals in stats_raw.items()
        }

        self.policy = SmolVLAPolicy.from_pretrained(str(ckpt_dir))
        self.policy = self.policy.to(device)
        self.policy.eval()
        self.policy.reset()

        self.preprocessor, _ = make_smolvla_pre_post_processors(
            config=self.policy.config,
            dataset_stats=stats,
        )

        self.task_prompt = task_prompt
        self.stats       = stats
        self.device      = device
        self.image_key   = "observation.images.top"
        self.state_key   = "observation.state"
        self.action_key  = "action"
        print(f"[SmolVLAPolicy] Loaded from {checkpoint_path}")
        print(f"[SmolVLAPolicy] Task prompt: '{task_prompt}'")

    def predict(self, obs: dict) -> np.ndarray:
        """
        Run one inference step.

        Parameters
        ----------
        obs["image"]:  (C, H, W) float32 in [0, 1], RGB channel-first
        obs["state"]:  (NUM_JOINTS,) float32 joint angles in radians

        Returns
        -------
        np.ndarray, shape (NUM_JOINTS,), joint angles in radians
        """
        image = torch.from_numpy(obs["image"]).float()  # (C, H, W)
        state = torch.from_numpy(obs["state"]).float()  # (NUM_JOINTS,)

        single_obs = {
            self.image_key: image,
            self.state_key: state,
            "task": self.task_prompt,
        }

        batch = self.preprocessor(single_obs)

        with torch.no_grad():
            action_norm = self.policy.select_action(batch)

        eps = 1e-8
        act_mean = self.stats[self.action_key]["mean"].to("cpu")
        act_std  = self.stats[self.action_key]["std"].to("cpu")
        action   = action_norm.cpu() * (act_std + eps) + act_mean

        a = action.numpy()
        if a.ndim == 2:
            a = a[0]
        return a.flatten()[:constants.NUM_JOINTS].astype(np.float32)

