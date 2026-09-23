# Session log — 2026-09-21/22 (continued) — getting stacking to work on the real DOFBOT Pro

Continues `session_log_2026-09-21.md` (architecture, tasks, pipeline). Nothing committed; all changes are uncommitted
working-tree changes. Focus moved from the full Verify2Act pipeline to making **basic stacking** (`task3a`-style,
green on red) work reliably, using a direct test script without VLM/critic/WM.

---

## 1. Decisions made
- **Stacking is kept** (it's the task where a rejected plan is most obviously useful), but bin tasks are the reliable
  headline tasks. Two new bin presets were added (§3).
- **Home the arm only when a task starts**, never between the subtasks of a task (user's explicit requirement).
- **Stacking motion** (user's spec): pick → lift → move above the target (cached position) → lower → release.
- **No fixed drop nudge** (e.g. "1 cm left"): it's layout-dependent and wrong for mirrored layouts.
- Stacking debugged with `verify2act/stack_test.py` (direct, no pipeline).

## 2. Bin task
- New bin drop pose (from the user, confirmed working): `left_bin = [170, 40, 50, 30, 90, 135]` — now the code default
  for `left_bin`, `left`, `storage_bin`, `default` in `lang_color_grasp.py`.
  (My earlier suggestion `[150, 55, 34, 16, 90, 145]` did not lift the object — discarded.)

## 3. Task presets added (`v2a_pipeline.py::TASK_PRESETS`)
| id | goal |
|---|---|
| `task1c` | "Clear all warm-colored blocks into the bin and leave the green block" (red + yellow move, green stays) |
| `task1d` | "Put the red block, the green block and the blue block into the bin except the yellow block" (3 move, 1 stays) |
Both parse correctly with `parse_goal`. `built_in_policy.md` lists them. Not yet run on the robot.

---

## 4. Code changes (this session)

### `dofbot_pro_voice_ctrl/scripts/Color/lang_color_grasp.py`
- **New actions**: `locate` (detect a block from the observation pose, cache its world pose, don't move),
  `reset` (home the arm; sent once at task start). `place_on` uses the cached base pose (< 5 min old) instead of
  detecting the base while holding a block; cache cleared after the place.
- **Pick (`_grasp_and_hold`)**: approach from above (shoulder-raised pre-grasp, then straight down), close, then lift by
  rotating the shoulder up `~lift_j2_deg` (default 20°) and **stay there** (no homing, no bin-height lift).
  A Cartesian "straight up 8 cm" lift was tried first and failed: at ~24 cm reach the IK swung the wrist and knocked the
  block over.
- **Place (`place_on`)**: release pose = IK at `~stack_dz` (0.05 m, the value that stacked) above the cached base
  (+ `~stack_dx`, `~stack_dy`, wrist `~stack_dyaw`); approached via the same pose with shoulder raised; release; rise;
  home (end of task, so the eye-in-hand camera sees the result).
- **`_ik()`**: default gripper pitch (Roll −1.047); if joint 3 < 0 (block close to the base, servo can't go below 0),
  steepen pitch in 0.05 rad steps.
- **`_send_joints()`**: every full-arm move is checked against `/joint_states` and re-sent (≤2 times) if any joint is
  > 4° off; logs `joints off target (joint: (actual, target))`.
- **`_safe_home()`**: home in stages — joint 2 → 90 (arm straight), joint 2 → 120 (still straight), then fold joints
  3–5. Verified with FK: gripper never below ~9 cm. (Folding at joint 2 = 90 swept the gripper to ~4 cm high, 8 cm from
  the base axis → **hit the robot base**; a one-shot home from a stretched pose stalled joint 2.)
- `subtask_done` now includes the block world `pose`. Log line `place_on release: joint1 target X, actual Y`.
- Optional, off by default: `~j1_approach_deg`, `~j1_trim_deg`, `~place_two_stage`, `~ik_lower_on_saturation`,
  `~pick_hold_mode`-style variants were tried and reverted/disabled.

### `dofbot_pro_voice_ctrl/scripts/Color/lang_color_detect.py`
- Edge guard: ignore blobs with centre within 20 px of left/right/top edge or below y = 420 (false green blobs at the
  bottom edge had sent the arm to wrong places).
- Search timeout (`~search_timeout`, 25 s): gives up, publishes `subtask_done {"status":"error"}` — previously a late
  lock-on started a pick minutes after the caller had given up.
- Own blob finder `_find_blob()` (same logic as `object_follow`); **red also takes hue 0–8** (red wraps the hue circle;
  the 160–180 range alone caught only speckles → centre off by up to ~2 cm). Hue 0–10 is NOT safe: the wooden table
  (hue 9–14) became the largest "red" blob in 11/21 frames; 0–8 was clean in 21/21.

### `dofbot_pro_voice_ctrl/scripts/Color/green_colorHSV.text`
- `35, 80, 40, 90, 255, 255` → **`35, 40, 40, 90, 255, 255`** (S floor 80 → 40). Under the table's lighting the green
  top face on the right side of the sheet has S ≈ 44–80, so only far-end specks matched and the arm grasped the tip of
  the block. With S ≥ 40 the aim point is mid-block in all trial frames; paper/table excluded by hue.

### `dofbot_pro_info/scripts/arm_driver.py`
- **I2C bus lock** around servo writes and the 20 Hz read-back loop. They shared the bus unsynchronized and writes were
  silently dropped (seen: joint 3 ignoring a home, joint 2 staying at 121° when sent to 11° → the "arm swings high
  before coming down" behaviour). Dropped writes still occur occasionally; `_send_joints` catches them.

### `verify2act/`
- `v2a_pipeline.py`: `reset` before the first observation; for stack goals, `locate <base>` before the `pick`.
- `v2a_robot_client.py`: `capture_frame` drops frames stamped before the call (clock offset estimated from the stream).
  NOTE: the "ceiling" frame that motivated this was actually the arm not reaching home (dropped joint-3 write), not a
  stale frame.
- `v2a_world_model.py` (stub critic masks): red also hue 0–8 with S ≥ 190, V ≤ 110 (shaded red under a stacked block).
- **`stack_test.py`** (new): `reset → locate base → pick top → place → home → locate top`.
  `--trials N`: prompts to rearrange blocks, asks y/n + note, writes `results/stack_test/<time>/trials.jsonl`,
  `summary.md` (positions, measured placement error = top_after − base, outcome), frames per run
  (`0_before`, `0b_holding`, `1_after`).

---

## 5. What we found (evidence)

### Stacking trials (`verify2act/results/stack_test/`)
| session | result | main failures |
|---|---|---|
| `20260922_010912` | 6/10 | picks grasped the block tip (washed-out green → S floor fix); run 10 detector never locked |
| `20260922_014025` | 6/10 | all picks OK; placements fell when red was far right (x ≈ +4.1 cm) |
| `20260922_023141` | 4/10 | right-side placements fell again; picks at the reach edge failed (servo stalls) |

**Combined last two sessions (20 runs):**
- **Red block at x ≥ +3.9 cm (right of image, pixel x ≳ 440): 0/7 stacked** — green lands ~2 cm toward the centre
  (left) and falls. Detection there is clean, joints reach targets (j1 within 1°), IK is exact (FK check) → the error is
  in pixel→world mapping near the right image edge (camera/hand-eye calibration or depth-colour registration).
  Not fixed.
- **Red block at x ≤ +3 cm: 10/13 stacked**; measured placement errors −0.7 … +0.6 cm. Remaining failures: patchy red
  detection (fixed since), picks at the edge of reach, servo stalls.
- Far left (x = −8.4 cm) landed ~1.5 cm toward the right (user) — same "toward centre" trend, smaller.
- Best placement: both blocks near the centre line (x ≈ 0), r 0.18–0.27.
- Joint-1 gear slack hypothesis was **wrong** (read-back j1 within 1° of target everywhere).
- Tilt of the placed block remains (not addressed; partly from off-centre grasps).

### Hardware limits
- **Servo torque**: joint 3 can't hold 90° (arm straight out) at far reach; joint 2 can't lift a held block from low,
  stretched poses (e.g. 39° instead of 91°). Worse after long sessions (servo heat). The pick-from-above pre-grasp adds
  the heaviest pose for far picks (run 5 of `023141`: arm folded toward the base instead of reaching).
- **Reach**: IK saturates joint 3 at 90° beyond ~24–25 cm (FK says the pose still reaches, and stacks worked there);
  below ~19–20 cm joint 3 goes negative (steeper-pitch fallback now handles it).
- Intrinsics hard-coded in `lang_color_grasp.py` differ < 1% from `/camera/color/camera_info` (fx 480.9, cx 320.5) —
  negligible (~0.3 mm).
- `dabai_dcw2.launch` has `depth_registration` changed false → true (pre-existing uncommitted change) — suspect for the
  edge error, not verified.

### Mistakes corrected during the session
- Homing after the pick (bin-lift then home) caused "way up then home" — removed.
- "Blocks too close to the base" and "IK unreachable" explanations were wrong; real causes were a false detection at
  the frame edge and my auto-lowering of the hover.
- It was midday (Jetson clock is UTC+8), not night.

---

## 6. Open options (awaiting user decision)
- **A (recommended for experiments):** restrict the workspace to where it works — both blocks r 0.20–0.26 m, red
  x ∈ [−0.085, +0.03] m (image pixel x < ~430), green |x| ≤ 0.05 m; add a check in `stack_test` / pipeline that warns
  or refuses outside it. Report as the workspace definition in the paper.
- **B:** fix the right-side pixel→world error properly (hand-eye check with ground-truth points, e.g. block tags or
  sheet marks), then re-test the full width.
- **C:** reduce servo strain — smaller approach lift for far picks, avoid IK solutions with joint 3 at 90°.
- Suggested next: A + C, then 10-episode `task3a` sessions inside the zone; B if a wider workspace is needed.

## 7. Still open from the previous log
- Run `task1a/1b/1c/1d` sessions (10 episodes, labelled); `task1c/1d` not yet run on the robot.
- Real WM/critic server (`robot_server.py` in `~/echris/verify2act`, branch `robot-server`, commit `90355e1`, not pushed)
  with checkpoints; VLM location (Jetson vs server).
- Commit strategy for this repo (nothing committed); outdated section in `verify2act/DEMO_GUIDE.md`.
- The full pipeline (`v2a_pipeline.py`) was not re-run after the stacking changes; its stub critic's red mask differs
  from the detector's.

## 8. System state at end of session
- Running (background, logs in `/tmp/claude-1000/`): roscore, `arm_driver.py` (restarted with the bus lock), camera,
  kinematics, rosbridge, `lang_color_detect.py`, `lang_color_grasp.py` — all with the changes above. Arm at home.
- Live rosparam: `/lang_color_grasp/stack_dx = 0.0` (all other tunables at code defaults).
- Restart a node safely with `rosnode kill /lang_color_grasp` (not `pkill -f`, which can kill the calling shell).
  Restarting `arm_driver.py` moves the arm to `[90, 80, 45, 0, 90, 30]`; `lang_color_grasp.py` homes on start.
- Commands:
  ```
  python3 verify2act/stack_test.py --top green --base red                # one run
  python3 verify2act/stack_test.py --top green --base red --trials 10    # labelled trials (run in your own terminal)
  rosparam set /lang_color_grasp/{stack_dz,stack_dx,stack_dy,stack_dyaw,lift_j2_deg} <value>   # live tuning
  ```
