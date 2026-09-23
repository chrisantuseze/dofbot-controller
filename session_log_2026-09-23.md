# Session log — 2026-09-23 — bin tasks: pipeline re-verified, stub red mask fixed

Continues `session_log_2026-09-22.md`. Decision this session: **leave stacking where it is** (option A/B/C in §6
of the previous log are still open) and **move on to the bin tasks** (`task1a`–`task1d`), which are the reliable
headline tasks. No robot motion this session — everything below is dry-run / offline analysis.

---

## 1. Pipeline re-verified after the stacking refactor
Open item §7 of the previous log ("the full pipeline was not re-run after the stacking changes") is closed.

- The bin path `lang_color_grasp._move_and_deposit()` is **untouched** by the stacking work: it is only reached for
  `action = pick_place`, while the reworked code lives in the `pick` / `place_on` branches.
- All four presets parse correctly:

  | task | goal | plan |
  |---|---|---|
  | `task1a` | blue + yellow → bin | 2 horizons |
  | `task1b` | cool colours → bin, leave yellow | blue, green |
  | `task1c` | warm colours → bin, leave green | red, yellow |
  | `task1d` | red + green + blue → bin, except yellow | 3 horizons |

- `task1c` / `task1d` verify end-to-end for the first time (they were added last session but never run).

## 2. The `task1b` flake, and what it actually was

**Symptom.** The first `task1b --dry_run` rejected horizon 2 (green) with *"unrelated red block changed"* on all three
replans, so the replan budget was exhausted and nothing would have executed. In a session that scores as
`verified = False` → `real_success` auto-labelled `False`, i.e. a critic artefact recorded as a robot failure.

**Not reproducible**: 0 failures in 25 fresh-process `task1b` dry runs, and 20/20 frames verified for all four tasks.

**Two wrong hypotheses, both discarded on evidence:**
- *The world model's inpaint box overlaps the red block.* Traced 25 frames: 0 multi-iteration erases, 0 cross-colour
  clashes. Red's fragments all sit on the red block (x 55–182); green/blue/yellow are at x ≥ 240.
- *The red mask is ~42% stray pixels (shadow / tag), so a removed block still reads "on the table".* Wrong reading.
  Rendering the mask over the frame showed the fragments are **on the red block itself** — the mask simply covers it
  patchily. A `block_area()` helper written on this premise was added and then **reverted** (see §4).

**Real cause.** The stub's red mask covered only **26%** of the red block where the robot's own detector covered
**64%**, because the two build the hue wrap-around band differently:

| | red band |
|---|---|
| `lang_color_detect._find_blob` | calibrated `160,110,90–180,255,255` **+ `(0,110,90)–(8,255,255)`** (reuses the calibrated S/V floors) |
| `v2a_world_model.color_mask` (before) | calibrated range **+ `(0,190,30)–(8,255,110)`** only (the narrow "shaded red" band added for stacking) |

With only a quarter of the block matched, red's pixel count was marginal and unstable, which is the quantity the
`KEEP_FRACTION = 0.7` "unrelated block changed" test is applied to. This is exactly the §7 note
*"its stub critic's red mask differs from the detector's"*.

## 3. Fix
`verify2act/v2a_world_model.py :: color_mask()` — for red, the 0–8 band now reuses the calibrated S/V floors,
mirroring `lang_color_detect._find_blob` exactly; the narrow shaded-red band is kept on top (it covers red under a
stacked block, below the calibrated V floor). Hue stays ≤ 8: the wooden table is hue 9–14.

Measured on the live camera, same scene:

| | before | after |
|---|---|---|
| red mask on the red block | 4 880 px | 12 487 px |
| red count spread over 15–20 frames | **18.6 %** | **2.1 %** |
| green / blue / yellow spread | 7.5 / 1.8 / 0.9 % | 5.3 / 0.9 / 1.5 % |

**Not claimed:** that the original flake is proven fixed — it never reproduced, so there is nothing to re-test
against. What is established is that the mechanism it depended on (a marginal, unstable red count) is gone.

`verify2act/v2a_critic.py` also now logs the two pixel counts in that rejection
(`unrelated red block changed (4880 -> 2100 px)`), so if it recurs during a session the logs give the cause instead
of another guess.

**The detector was deliberately left alone.** Loosening `red_colorHSV.text` from `160,110,90` to `160,90,50` would
raise block coverage 64% → 72% but multiplies false pixels 142 → 2 863 (the table bleeds in). Not worth it; the
largest blob already lands on the red block in 15/15 frames with the current values.

## 4. Reverted
`block_area()` (largest-blob area instead of whole-mask count) was added to `v2a_world_model.py` and wired through the
critic and planner, then removed. It rested on the mistaken "42% stray" reading; after the mask fix the numbers do not
support it (red raw spread 2.1% vs block-area spread 6.4%), and taking only the largest blob would misread a block
split by the arm's shadow as "moved". Net change set this session is §3 only.

## 5. Validation (all offline / dry-run)
- goal head accepts a **real** successful finish for all four tasks (block regions blanked as the arm carrying them
  away would leave the scene); red now reads 39 px after removal, well under `MIN_BLOCK_PIXELS = 300`.
- negative controls still reject: target block never moved; a "leave it" block moved.
- 15/15 frames verified per task; 12/12 fresh-process dry runs across the four tasks (3 each).

## 6. Next
- Run the labelled sessions (10 episodes each, interactive — needs a human at the keyboard for scene reset + y/n):
  ```
  python3 verify2act/v2a_session.py --task task1a --episodes 10 --local
  ```
  `--local` uses rospy directly; rosbridge is only needed for the remote WM/critic.
- Still open from previous logs: the right-side stacking calibration error (§6 B of 2026-09-22), the real WM/critic
  server, the commit strategy for this repo (nothing committed yet), the outdated section of `verify2act/DEMO_GUIDE.md`.

## 7. System state
roscore, `arm_driver.py`, camera, kinematics, `lang_color_detect.py`, `lang_color_grasp.py` all running; rosbridge not
started. Arm at home, never commanded this session. No rosparam overrides set — all tunables at code defaults.
ROS env for a shell: unset `PYTHONPATH`/`LD_LIBRARY_PATH`, then source `/opt/ros/noetic/setup.bash` and
`dofbot_pro_ws/devel/setup.bash` (ROS 2 foxy on the default path otherwise shadows `rosgraph_msgs`).

---

# Session log — 2026-09-23 (later) — inconsistent bin grasping: two defects in the deposit path

Symptoms reported after running a real `task1c` session
(`verify2act/results/task1c_20260923_222929`, 3/10 real success): sometimes the arm grasps a block and
**drags** it to the bin without lifting; sometimes it lifts and then **drops the block mid-way** while
lowering; sometimes everything works.

## Evidence
`/home/jetson/.ros/log/lang_color_grasp.log` — 57 `joints off target` warnings, 10 of them `giving up`
(the sequence then continues anyway). Joint 2 missed by up to 68° (`{2: (52.0, 120.0)}`, failing to reach
the home lift), joint 3 by 72° (`{3: (18.0, 90.0)}`, the known saturation pose).

Tonight's session alone: **8 subtasks, 5 off-target events, three of them identical** —
`{2: (120.0, 40.0)}; re-sending`. Joint 2 was told to lower into the bin and was still at exactly 120 (the
value step 3 had put it at) 2.4 s later. Each recovered only because `_send_joints` re-sent it.
So roughly **one bin descent in three needed a second command before joint 2 moved at all.**

## Defect 1 — the deposit was almost entirely unverified
`_move_and_deposit()` has 8 steps; only step 5 sent a full joint array. `pub_arm` routes to the checked
`_send_joints` **only** when given a non-empty joints list — the `id=`/`angle=` single-servo form publishes
once and never reads back. So the dropped-write protection added on 2026-09-22 covered exactly one step.

Step 3 (the lift, `id=2 -> 120`) is the same joint and the same move under load as the descent that
demonstrably needs a re-send a third of the time — but on the unverified path. When it does not take,
nothing notices and step 4 rotates the base with the block still on the table: **the dragging failure.**

## Defect 2 — the bin preset opened the gripper during the descent
`DROP_PRESETS["left_bin"] = [170, 40, 50, 30, 90, 135]`; the 6th value is a **gripper angle**, and
`arm_driver.Armcallback` writes all six servos (`Arm_serial_servo_write6(msg.joints[0..5])`). With the block
held at `gripper_close_angle = 145`, step 5 therefore commanded the grip open by 10° *while lowering into the
bin* — before the intended release at step 6: **the mid-way drop.**

Intermittent because it depends on the grasp: a deep square grasp closes at a smaller angle so 135 is still
past contact and holds; a shallow or corner grasp contacts later and 135 clears it. **Not measured** — the
unintended gripper command is certain from the code, the contact-angle geometry is inference. One test
settles it: close on a block at 145, read `grip_joint` from `/joint_states`, command 135, see if it slips.

## Fixes (all in `lang_color_grasp.py`, nothing else touched)
1. `_send_joints()` now returns a bool (True when there is no read-back to judge by); `pub_arm` /
   `pub_target_arm` pass it through. Backward compatible — existing callers ignore it.
2. New `_hold_pose()` / `_carry_move()`: every step taken **while the block is held** (lift, base turn) is
   sent as a full pose built from the measured arm pose with one joint overridden, so it goes through
   `_send_joints` and gets read back and re-sent. Only the named joint is really under test; the others are
   commanded to where they already are. Falls back to the old single-servo write if `/joint_states` has not
   arrived.
3. Step 5 sends `drop_joints[:5] + [gripper_close_angle]` — the grip is kept until step 6 releases it.
4. A carrying step that never lands now raises, which the existing handler turns into
   `subtask_done {"status": "error"}` → `execute_subtask` returns False → the episode ends. Previously
   `_execute_grasp_pipeline` published `status: success` whenever no exception was raised, including after
   `giving up`: 118 subtasks triggered across the log, 111 reported success, so a stalled lift was
   indistinguishable from a real one in the session statistics.

**Deliberately scoped:** give-up was NOT made fatal globally. Joint-3-at-90 saturation give-ups happen in the
stacking (`place_on`) path, where the 2026-09-22 log records stacks succeeding anyway; making those fatal
would break stacking. Only the bin deposit's carrying steps treat a failed move as fatal, and
`_move_and_deposit` is reached only for `pick_place`, so the stacking path is untouched.
Step 7 (raise clear of the bin) warns but does not raise — the block is already released and `_safe_home`
stages the lift itself. The gripper close (step 2) stays unverified on purpose: the jaws stall on the block
well before `gripper_close_angle`, so a read-back would never match and would retry on every grasp.

Also corrected a misleading comment: step 1's `id=5` is `Arm5_Joint` (the wrist), not the gripper (`id=6`);
the gripper was already opened to 30 by the approach pose.

## Verified
Offline unit checks against a stub (no arm motion): `_hold_pose` builds the expected arrays; a stalled lift
raises and **no base turn follows**; a good lift sends one full pose; the no-`/joint_states` fallback emits
the old single-servo write; step 5's gripper value is 145, not 135.

**Not yet verified on the robot.** `lang_color_grasp.py` must be restarted to load the changes
(`rosnode kill /lang_color_grasp`, then relaunch — it homes on start, so the arm moves). The open question
that the logs cannot settle: whether joint 2 is *dropping the write* or *stalling under torque*. It read
exactly 120.0 rather than an intermediate angle, and `Armcallback` already issues each write twice, which
leans toward a stall — but fix 2 handles both.
