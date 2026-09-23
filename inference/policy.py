#!/usr/bin/env python3
"""
policy.py
=========
Language-Conditioned Action Chunking Transformer (ACT) Policy for DofBot Pro.

Architecture:
- Vision Encoder: Pretrained ResNet-18 backbone (extracts visual tokens from top camera).
- Language Conditioning: Task/Instruction embedding module mapping commands into latent tokens.
- State Projector: Linear embedding for 6-DoF joint state.
- CVAE Latent Model: Encodes action chunks + observation during training for multi-modal trajectories;
  at inference time, samples or uses mean latent z = 0.
- Transformer Decoder: Cross-attends visual, state, language, and latent tokens to predict
  the H-step future joint action chunk.
"""

import math
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

NUM_JOINTS = 6


class SinusoidalPositionEmbedding(nn.Module):
    def __init__(self, dim: int, max_len: int = 512):
        super().__init__()
        pe = torch.zeros(max_len, dim)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, dim, 2).float() * (-math.log(10000.0) / dim))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))  # (1, max_len, dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, SeqLen, Dim)
        return x + self.pe[:, :x.size(1)]


class LanguageACTPolicy(nn.Module):
    """
    Action Chunking Transformer (ACT) conditioned on Vision, Robot State, and Language.
    """

    def __init__(
        self,
        chunk_size: int = 16,
        state_dim: int = 6,
        action_dim: int = 6,
        num_tasks: int = 16,
        dim_model: int = 256,
        nhead: int = 4,
        num_encoder_layers: int = 2,
        num_decoder_layers: int = 2,
        dim_feedforward: int = 512,
        latent_dim: int = 32,
        use_vae: bool = True,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.chunk_size = chunk_size
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_tasks = num_tasks
        self.dim_model = dim_model
        self.use_vae = use_vae
        self.latent_dim = latent_dim

        # ── 1. Vision Backbone (ResNet-18) ──────────────────────────────────
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        # Remove avgpool and fc, keep conv feature map
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        # ResNet18 output is 512 channels -> project to dim_model
        self.visual_proj = nn.Conv2d(512, dim_model, kernel_size=1)

        # ── 2. State & Language Embeddings ──────────────────────────────────
        self.state_proj = nn.Linear(state_dim, dim_model)
        self.lang_embedding = nn.Embedding(num_tasks, dim_model)

        # ── 3. CVAE Encoder (for training action distribution) ──────────────
        if self.use_vae:
            self.action_proj = nn.Linear(action_dim, dim_model)
            self.cvae_cls_token = nn.Parameter(torch.randn(1, 1, dim_model) * 0.02)
            cvae_layer = nn.TransformerEncoderLayer(
                d_model=dim_model, nhead=nhead, dim_feedforward=dim_feedforward,
                dropout=dropout, batch_first=True
            )
            self.cvae_encoder = nn.TransformerEncoder(cvae_layer, num_layers=2)
            self.cvae_mu = nn.Linear(dim_model, latent_dim)
            self.cvae_logvar = nn.Linear(dim_model, latent_dim)
            self.latent_proj = nn.Linear(latent_dim, dim_model)
        else:
            self.latent_proj = None

        # ── 4. Action Decoder ───────────────────────────────────────────────
        self.pos_emb = SinusoidalPositionEmbedding(dim_model, max_len=128)
        self.action_queries = nn.Parameter(torch.randn(1, chunk_size, dim_model) * 0.02)

        decoder_layer = nn.TransformerDecoderLayer(
            d_model=dim_model, nhead=nhead, dim_feedforward=dim_feedforward,
            dropout=dropout, batch_first=True
        )
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers=num_decoder_layers)
        self.action_head = nn.Linear(dim_model, action_dim)

    def encode_observations(
        self,
        image: torch.Tensor,
        state: torch.Tensor,
        task_id: torch.Tensor,
    ) -> torch.Tensor:
        """
        Extract and fuse visual, state, and language tokens into context memory.
        
        Args:
            image: (B, 3, H, W)
            state: (B, state_dim)
            task_id: (B,)
        Returns:
            memory: (B, num_tokens, dim_model)
        """
        B = image.size(0)

        # Visual tokens: (B, 512, h, w) -> (B, dim_model, h, w) -> (B, h*w, dim_model)
        feat = self.visual_proj(self.backbone(image))
        vis_tokens = feat.flatten(2).transpose(1, 2)  # (B, h*w, dim_model)

        # State token: (B, 1, dim_model)
        state_token = self.state_proj(state).unsqueeze(1)

        # Language token: (B, 1, dim_model)
        lang_token = self.lang_embedding(task_id).unsqueeze(1)

        # Context memory: [State, Language, Visual tokens...]
        memory = torch.cat([state_token, lang_token, vis_tokens], dim=1)
        return memory

    def forward(
        self,
        batch: Dict[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Training forward pass computing L1/L2 action reconstruction loss + KL loss.
        """
        image = batch["observation.images.top"]
        if image.dim() == 5:
            image = image.squeeze(1)  # (B, 3, H, W)
        
        state = batch["observation.state"]
        if state.dim() == 3:
            state = state.squeeze(1)  # (B, 6)

        actions = batch["action"]     # (B, chunk_size, 6)
        task_id = batch["task_id"]    # (B,)
        pad_mask = batch.get("action_is_pad", None)  # (B, chunk_size)

        B = image.size(0)

        # Encode context tokens
        memory = self.encode_observations(image, state, task_id)

        # CVAE Latent Sampling
        if self.use_vae:
            action_tokens = self.action_proj(actions)  # (B, chunk_size, dim_model)
            cls_token = self.cvae_cls_token.expand(B, -1, -1)
            cvae_input = torch.cat([cls_token, memory, action_tokens], dim=1)
            cvae_out = self.cvae_encoder(cvae_input)
            cls_out = cvae_out[:, 0]  # (B, dim_model)

            mu = self.cvae_mu(cls_out)
            logvar = self.cvae_logvar(cls_out)
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            z = mu + eps * std  # Reparameterization

            z_token = self.latent_proj(z).unsqueeze(1)  # (B, 1, dim_model)
            memory = torch.cat([z_token, memory], dim=1)

            # KL Divergence Loss
            kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=-1).mean()
        else:
            kl_loss = torch.tensor(0.0, device=image.device)

        # Transformer Action Decoding
        tgt = self.action_queries.expand(B, -1, -1)  # (B, chunk_size, dim_model)
        tgt = self.pos_emb(tgt)
        dec_out = self.decoder(tgt=tgt, memory=memory)
        pred_actions = self.action_head(dec_out)     # (B, chunk_size, action_dim)

        # Reconstruction Loss (L1 + L2)
        if pad_mask is not None:
            mask = (~pad_mask).unsqueeze(-1).float()  # (B, chunk_size, 1)
            l1_loss = (F.l1_loss(pred_actions, actions, reduction="none") * mask).sum() / (mask.sum() * NUM_JOINTS + 1e-6)
            l2_loss = (F.mse_loss(pred_actions, actions, reduction="none") * mask).sum() / (mask.sum() * NUM_JOINTS + 1e-6)
        else:
            l1_loss = F.l1_loss(pred_actions, actions)
            l2_loss = F.mse_loss(pred_actions, actions)

        total_loss = l1_loss + 0.5 * l2_loss + 0.01 * kl_loss

        loss_dict = {
            "loss": total_loss.item(),
            "l1_loss": l1_loss.item(),
            "l2_loss": l2_loss.item(),
            "kl_loss": kl_loss.item() if isinstance(kl_loss, torch.Tensor) else kl_loss,
        }
        return total_loss, loss_dict

    @torch.no_grad()
    def select_action(
        self,
        image: torch.Tensor,
        state: torch.Tensor,
        task_id: Union[int, torch.Tensor],
    ) -> torch.Tensor:
        """
        Inference step: predicts chunk_size future actions given observation & task.
        
        Args:
            image: (1, 3, H, W) normalized float tensor
            state: (1, 6) normalized float tensor
            task_id: int or (1,) tensor
        Returns:
            predicted_actions: (chunk_size, 6) tensor
        """
        self.eval()
        device = next(self.parameters()).device

        if image.dim() == 3:
            image = image.unsqueeze(0)
        if state.dim() == 1:
            state = state.unsqueeze(0)
        if isinstance(task_id, int):
            task_id = torch.tensor([task_id], dtype=torch.long, device=device)
        elif task_id.dim() == 0:
            task_id = task_id.unsqueeze(0)

        image = image.to(device)
        state = state.to(device)
        task_id = task_id.to(device)
        B = image.size(0)

        memory = self.encode_observations(image, state, task_id)

        if self.use_vae:
            # Zero latent vector prior at inference
            z = torch.zeros(B, self.latent_dim, device=device)
            z_token = self.latent_proj(z).unsqueeze(1)
            memory = torch.cat([z_token, memory], dim=1)

        tgt = self.action_queries.expand(B, -1, -1)
        tgt = self.pos_emb(tgt)
        dec_out = self.decoder(tgt=tgt, memory=memory)
        pred_actions = self.action_head(dec_out)  # (B, chunk_size, 6)

        return pred_actions.squeeze(0)  # (chunk_size, 6)
