# Session log — 2026-09-21 — Verify2Act on the real DOFBOT Pro

Goal: get the Verify2Act loop (VLM plan → world model imagination → critic → execute) running on the real robot for the RA-L
real-robot experiment, with the world model + critic hosted on a separate GPU machine.
Nothing in this repo was committed (all changes are uncommitted working-tree changes).

---

## 1. Architecture (agreed during the session)

| Where | What runs |
|---|---|
| **This Jetson Orin Nano** (~3 GB shared RAM) | ROS, camera, arm driver, `lang_color_detect`/`lang_color_grasp`, rosbridge, the orchestration loop (`v2a_pipeline.py` / `v2a_session.py`), VLM/planner (stub for now) |
| **GPU machine** (user's research repo, https://github.com/chrisantuseze/verify2act, branch `main-wm`; WM in `verify2act/latent_wm`, critic = DINOv2 dual-head in `verify2act/critic`) | World model + critic. Connects OUT to the Jetson's rosbridge with roslibpy (same pattern as `unveiler_inference_server.py`) |

Flow per timestep (mirrors `run_episode` in the research repo):
1. Jetson captures the real frame `S_t`.
2. VLM proposes a plan (subtask texts, e.g. `pick blue block`, `place blue block on yellow block`).
3. Jetson sends `evaluate_plan {image, goal, actions[], thresholds}` to the server. Server encodes to DINO features, rolls the
   latent WM forward horizon by horizon; temporal head (θ_c) compares consecutive states → `continue | requery` (rewind + re-imagine);
   after the last horizon the goal head (θ_p) compares the final imagined state with the language goal →
   `continue (accept) | requery (re-roll plan) | reflect`.
4. `reflect` → critic diagnosis (`ctx`) goes back to the VLM, which revises the plan (budget `max_replans`).
5. Accepted plan is executed on the arm (`full_plan` or `step_by_step`).
6. Jetson re-observes; `goal_check` (goal head on the REAL frame) decides done vs. re-plan.
Imagined states are latent tensors and stay on the server; images only come back with `--decoder-ckpt` (figures).

Not built yet: server-hosted VLM (`propose`/`reflect` ops returning the plan to the Jetson). Currently the VLM runs on the Jetson.

---

## 2. Physical setup facts
- Workspace: white sheet on a wooden table, coloured wooden bars (red/green/blue/yellow) on it.
- **One bin, to the robot's left, off-camera** (base joint 1 ≈ 150°). So "in the bin" = "block left the table" in the imagined frames.
- Camera: Orbbec, eye-in-hand; `/camera/color/image_raw/compressed` is NOT published → client falls back to raw.
- Jetson is an **Orin Nano**, ~0.7 GB free RAM with ROS+camera running → cannot host DINOv2-L + CLIP + dynamics.

## 3. Tasks (presets in `v2a_pipeline.py::TASK_PRESETS`)
| id | goal | tier |
|---|---|---|
| `task1a` | "Put the blue block and the yellow block into the bin" | multi-block, unnamed blocks must stay |
| `task1b` | "Clear all cool-colored blocks into the bin and leave the yellow block" | selective (green + blue move; yellow/red stay) |
| `task3a` | "Stack the blue block on top of the yellow block" (from `task_desc.md`) | ordering-constrained; H=2 (`pick`, `place_on`) |
Custom goals work via `--goal "..."` (e.g. "Stack the green block on top of the red block").

---

## 4. What was built / changed (this repo)

### New files
- `verify2act/v2a_goal.py` — goal/action parsing (`parse_goal`, `parse_stack`, `parse_step`), shared by planner + critic.
- `verify2act/v2a_decisions.py` — copy of the research repo's `check_rollout_consistency` / `decide_from_proximity` (θ_c=0.5, θ_p=0.6, conf=0.08).
- `verify2act/v2a_plan_eval.py` — `evaluate_plan()`: imagine+critic loop for one plan (used locally and by the stub server).
- `verify2act/v2a_robot_client.py` — `RemoteRobotClient` (roslibpy: camera + `/subtask_cmd`/`/subtask_done`/`/detect_status`, retries until the detector acknowledges) and `LocalRobotClient` (rospy).
- `verify2act/v2a_session.py` — **one session = one task × N episodes** (details §6).
- `verify2act/remote/{protocol,proxies,v2a_server}.py` — Jetson↔server protocol, proxies, and a **stub** server (colour-blob WM/critic) to test the round trip without a GPU.

### Rewritten
- `verify2act/v2a_pipeline.py` — receding-horizon loop, `--wm_server`, `--max_steps/--max_replans/--max_requery/--exec_mode`, thresholds, simulate flags, per-executed-action transition logging.
- `verify2act/v2a_world_model.py` — stub WM: removes the picked block (inpaint bbox, robust to fragmented masks), remembers the held block and renders `place_on`; fault injection removes the *wrong* block / places beside the base.
- `verify2act/v2a_critic.py` — stub critic exposing the research critic's interface `(mean, std)`; image-based (colour-blob) checks, never reads WM metadata. Temporal: target gone, others unchanged, `place_on` needs the block to be "held" first (ordering violation) and to land on the base footprint. Goal: `move`/`keep` sets or stack-on check vs the initial real frame.
- `verify2act/v2a_vlm_planner.py` — stub VLM with `propose(obs, goal, history)` / `reflect(obs, goal, history, old_plan, ctx)`; `--simulate_reprompt` makes proposal #1 flawed (wrong extra block / forgotten block / stack reversed = base picked first).

### Modified
- `dofbot_pro_ws/src/dofbot_pro_voice_ctrl/scripts/Color/lang_color_grasp.py`
  - live-tunable drop pose: `rosparam set /lang_color_grasp/drop_left_bin "[150,60,30,16,90,135]"`
  - new actions `pick` (grasp, lift, return to observe pose holding) and `place_on` (detect base, hover at `stack_dz`, release, retreat); `stack_dz` default 0.05 m: `rosparam set /lang_color_grasp/stack_dz 0.05`
  - `LanguageGraspClient.execute_subtask(..., action, base_color)`
- `dofbot_pro_ws/src/dofbot_pro_voice_ctrl/scripts/Color/green_colorHSV.text` — V floor **80 → 40** (`35, 80, 40, 90, 255, 255`); the dark green block (V≈66) was invisible to the detector.
- `built_in_policy.md` — commands appended (session, single episode, drop/stack tuning, server usage).
- `verify2act/DEMO_GUIDE.md` — a "Verify2Act pipeline" section was appended early in the session; **now outdated** (still shows the old single-episode commands) — prefer `built_in_policy.md`.

### Research repo (GPU-machine side)
`~/echris/verify2act`, branch `robot-server` (from `origin/main-wm`), **local commit `90355e1`, not pushed**:
- `verify2act/robot/robot_server.py` — real server (LatentWorldModel/RLAWorldModel + DINOv2DualHeadCritic), ops `ping | reset | evaluate_plan | goal_check`, mirrors `BeamSearchPlanner._evaluate_trajectory` (latent path).
- `verify2act/robot/test_robot_server.py` — 6 logic tests with fake WM/critic (all pass; on the Jetson `diffusers` must be stubbed before import).
- `verify2act/robot/README_ROBOT.md`, `requirements.txt` (+ roslibpy).
- **Not run with real checkpoints** (none available here; the Jetson can't load them).

---

## 5. Real-robot runs and outcomes
| # | run | result |
|---|---|---|
| 1 | "Put the yellow block into the bin" (first end-to-end, remote client on loopback) | success, block landed in bin (user confirmed) |
| 2 | `task1b` (blue + green into bin, leave red) | executed in 1 attempt; user confirmed **blue and green landed fine** |
| 3 | `task1a` (blue + yellow) via the session runner, `--no_confirm` | robot reported success; not human-labeled (`verify2act/results/task1a_real_test/`) |
| 4 | `task3a` (blue on yellow) | not executed — blue/yellow were not on the sheet; critic correctly refused (no blue visible) |
| 5 | "Stack the green block on top of the red block" (open-loop version) | robot reported success but **green was NOT stacked** (false accept) |
| 6 | same, receding-horizon version, `--max_steps 2` | critic accepted; after execution the real-state check said "not yet", loop retried; **goal not reached** (green ended near where it was picked; blue got disturbed) |

Observed physical issues:
- **Bin drops**: block is dropped *close to* the bin and sometimes collides with the bin (robot doesn't know the bin location). Untested hypothesis: the drop pose sets gripper j6 = 135 while grasp closes to 145 → grip loosens while lowering. Try `drop_left_bin = [150, 55, 34, 16, 90, 145]`, and tune j2/j3 for height.
- **Stacking (`task3a`)**: the user diagnosed that the robot cannot **align the picked block on the target block**, so it always falls off (details + fix plan in §8).

Mid-session system-state changes to remember:
- Killed the old `color_detect_VC.py` and `color_grasp_VC.py` (they share `/voice_result` and `/xyz` topics and would double-move the arm). Restart them only if you stop the lang_* nodes.
- Started (background, logs in `/tmp/claude-1000/`): `rosbridge_websocket`, `lang_color_detect.py`, `lang_color_grasp.py` (it homes the arm when it starts). They keep running until reboot/kill.
- **Do not `pkill -f <name>` from the same shell command** — it matches (and kills) the shell itself; use `pgrep -f ... | xargs kill` or kill by PID.

---

## 6. How to run (current)
```
# Jetson stack (see built_in_policy.md): roscore, arm_driver, camera, kinemarics, rosbridge, lang_color_detect, lang_color_grasp
# One session = one task, N episodes; each episode: reset scene -> Enter -> run -> answer y/n (+ note) -> logged
python3 verify2act/v2a_session.py --task task1a --episodes 10 --jetson_ip 127.0.0.1
python3 verify2act/v2a_session.py --task task3a --episodes 10 --jetson_ip 127.0.0.1 --wm_server   # WM/critic on the GPU box
python3 verify2act/v2a_session.py --task task1b --episodes 3  --jetson_ip 127.0.0.1 --dry_run     # real camera, arm never moves
python3 verify2act/v2a_pipeline.py --goal "Stack the green block on top of the red block" --jetson_ip 127.0.0.1 --max_steps 2   # single episode
# GPU machine:
python3 -m verify2act.robot.robot_server --jetson_ip <JETSON_IP> --critic-ckpt ... --latent-wm-ckpt ... --encoder-ckpt ...
# Stub server (no GPU) on the Jetson to test the round trip:
python3 verify2act/remote/v2a_server.py --jetson_ip 127.0.0.1
```
Session output → `verify2act/results/<task>_<time>/`: `episodes.jsonl` (crash-safe), `transitions.jsonl` (real `image_t / action_text / image_t1`
rows in the research repo's schema → training data for the real-robot WM/critic), `ep_NNN/` (timelines, real frames), `summary.md/json`
(real success rate, verified rate, critic precision, false accepts, avg timesteps/replans/VLM calls, requeries, time).
Simulation flags: `--simulate_reprompt`, `--simulate_temporal_inconsistency`, `--simulate_uncertainty`.

---

## 7. Known limitations / caveats
- VLM, world model and critic here are **stubs**; the imagined frames are inpainted images with blocky edits (OK for verdicts, not for paper figures).
- Stub critic detects blocks by colour (HSV files + pure BGR); lighting changes fragment masks (fixed for erase, but keep in mind).
- Domain gap: released research checkpoints are sim-trained; real fine-tuning needs the logged transitions (+ goal images / success labels for the goal head).
- `critic.encode()` documents [0,1] input while `preprocess_image_for_critic` gives [-1,1] (research repo); the server avoids that path by using the WM's DINO preprocessing + `critic.encode_features`.
- The imagined-vs-real comparison is only done via the goal head on the real frame; no explicit fidelity metric yet.
- Camera compressed topic missing → ~1.2 MB/frame raw over rosbridge.

---

## 8. Stacking failure — diagnosis and planned fix (NOT implemented yet)

**Diagnosis (user):** after picking, the robot cannot align the held block on the target, so the block rests unstably and falls off.
Cause in code (`lang_color_grasp.py::_execute_grasp_pipeline`, `place_on` branch): the IK target is only the detected pixel centre of the base block
(+ `stack_dz`). It ignores (a) the yaw of the base block, (b) the yaw/offset of the block inside the gripper, (c) wrist joint 5, and it detects the base
*while holding the picked block* (may occlude the view / shift the pose). The blocks are long bars, so an unaligned drop tips off.

**Planned fix (proposed to the user, awaiting go-ahead for items 1–3; needs the user present to watch and tune):**
1. **Wrist alignment**: measure the base block's orientation in the image (e.g. `cv2.minAreaRect` on its HSV mask in `lang_color_detect`, publish angle with `/xyz`), and rotate joint 5 so the held block lies parallel to the base block (account for the yaw at which it was grasped).
2. **Locate the base block before the pick**: detect both blocks (xyz + angle) from the initial observation and cache them, so nothing has to be detected while the arm holds a block; blocks don't move between pick and place.
3. **Tunable offsets** via rosparam (`stack_dx`, `stack_dy`, `stack_dyaw`, next to `stack_dz`) so placement can be nudged live.
4. **Gentle release**: lower `stack_dz` toward the block height (start 0.05 m, reduce stepwise), slower descent, open gripper a bit at a time, retreat straight up.

**Test protocol for tomorrow:**
1. Run `pick` alone (`--goal` won't do this; use `rostopic pub /subtask_cmd std_msgs/String '{"action":"pick","color":"green","held":"green","target":"hold"}'` or the pipeline with a stack goal and watch) and check whether the block is still in the gripper after the arm returns to the observation pose.
2. If held: test `place_on` with the base block well within reach, tune `stack_dz`, then wrist yaw / x-y offsets.
3. Then run `task3a` with `--episodes N` and label real outcomes.

---

## 9. Tomorrow's checklist
- [ ] Confirm the stacking-fix plan (items 1–3 above) and implement it, then tune on the robot with the user present.
- [ ] Tune the bin drop pose (`drop_left_bin`) to stop collisions; try gripper 145 during the lowering.
- [ ] Decide whether the VLM should also live on the GPU server (add `propose`/`reflect` ops) or stay on the Jetson.
- [ ] Get the research checkpoints (critic, `latent_wm`, encoder, decoder) onto the GPU machine, run `robot_server.py`, and test with `--wm_server`; plan real-data fine-tuning from `transitions.jsonl`.
- [ ] Run full sessions (`--episodes 10`) for task1a, task1b, task3a with human y/n labels; collect `summary.md`.
- [ ] Decide whether to push branch `robot-server` in `~/echris/verify2act`, and whether/how to commit the dofbot-controller changes (nothing committed yet).
- [ ] Update or remove the outdated section in `verify2act/DEMO_GUIDE.md`.
