Pretrained ACT Quickstart

This file shows recommended commands to run a pretrained ACT policy with `lerobot_inference_server.py`.

Available public ACT checkpoints (as of March 2026)

- `lerobot/act_aloha_sim_transfer_cube_human` — transfer-cube task (6-DOF compatible via state padding)
- `lerobot/act_aloha_sim_insertion_human`     — peg insertion variant

Note: `lerobot/act_koch_real` is no longer publicly accessible (returns 401). Use the above instead.

Recommended commands

GPU (recommended — real-time inference):

```bash
conda activate dofbot_controller
python lerobot_inference_server.py \
  --policy_type pretrained \
  --pretrained_repo lerobot/act_aloha_sim_transfer_cube_human \
  --device cuda:0 \
  --inference_hz 5 \
  --image_height 224 \
  --image_width 224 \
  --move_time_ms 200
```

CPU-only (lower rate to avoid latency):

```bash
conda activate dofbot_controller
python lerobot_inference_server.py \
  --policy_type pretrained \
  --pretrained_repo lerobot/act_aloha_sim_transfer_cube_human \
  --device cpu \
  --inference_hz 1 \
  --image_height 224 \
  --image_width 224 \
  --move_time_ms 400
```

Notes and next steps

- Smoke test confirmed: policy loads and produces (6,) radian actions from a 224x224 image.
- The ALOHA checkpoint was trained on 14-DOF arms; state is padded/clipped to its expected dim automatically, and actions are clipped to the first 6 joints. For best results, fine-tune on Dofbot data.
- If you plan to fine-tune on real robot data, use `--policy_type act --checkpoint_path /path/to/checkpoint` after training.
- lerobot is installed in the `dofbot_controller` conda environment.