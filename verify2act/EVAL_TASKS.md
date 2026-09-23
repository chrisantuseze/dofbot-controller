# Verify2Act real-robot evaluation tasks

Tasks planned for evaluation on the DOFBOT Pro. Every task is a preset in `TASK_PRESETS`
(`verify2act/v2a_pipeline.py`). One session = one task, N episodes, a human y/n label after each episode.

```bash
python3 verify2act/v2a_session.py --task <task> --episodes 10 --jetson_ip 127.0.0.1
```

Results go to `verify2act/results/<task>_<timestamp>/` (`episodes.jsonl`, `summary.md`, `transitions.jsonl`).

## Task families

| family | skill chain | what the critic checks (from pixels) |
|---|---|---|
| 1 — Bin clearing | `pick_place` into the off-camera left bin, one per block | named blocks gone from the table, every other block still there |
| 2 — Rearrangement | `locate` reference → `pick` (hold) → `place_at` beside the reference | moved block on the correct side of the reference, 0.6–3.5 block widths away, level within one block height, other blocks unchanged |
| 3 — Stacking | `locate` base → `pick` (hold) → `place_on` the base | top block's centre inside the base block's footprint, other blocks unchanged |

## Tasks

| id | goal | family | plan length | status |
|---|---|---|---|---|
| task1a | Put the blue block and the yellow block into the bin | 1 | 2 | 09-24: 5/10 (6 verified) |
| task1b | Clear all cool-colored blocks into the bin and leave the yellow block | 1 | 2 | not run yet (09-24 session stopped before episode 1 finished) |
| task1c | Clear all warm-colored blocks into the bin and leave the green block | 1 | 2 | 09-23: 3/10, then 6/10 after the bin-deposit fixes (7 verified) |
| task1d | Put the red block, the green block and the blue block into the bin except the yellow block | 1 | 3 | 09-24: 3/3 |
| task2a | Put the red block to the left of the blue block | 2 | 2 | 09-24: 4/4 (an earlier 0/4 session ran a grasp node started before `place_at` existed) |
| task2b | Put the green block to the right of the yellow block | 2 | 2 | 09-24: 4/4 |
| task3a | Stack the blue block on top of the yellow block | 3 | 2 | **deferred** — placement alignment issues in deployment |

Counts are real successes / labeled episodes, from `verify2act/results/<task>_<timestamp>/episodes.jsonl`.
All runs so far use the **stub** world model and critic; the evaluation proper uses the real ones.

Tasks 1a–1d exercise the same skill and differ only in language (explicit colours, colour groups,
"leave"/"except" exclusions), so they test goal grounding more than manipulation.
Family 2 adds a spatial relation and a two-step hold-and-place.

## Scene setup

- All four blocks (red, green, blue, yellow) on the white sheet, fully visible from the home pose.
- **Family 1:** bin to the robot's left, off-camera. Randomise block positions between episodes.
- **Family 2:** leave ≥ 10 cm of empty sheet on the placement side of the reference block (blocks are ~4 cm wide;
  placement is ~7 cm centre-to-centre). Keep the target spot left of image x ≈ 440 px (world x ≤ +3 cm),
  where placements are known to land ~2 cm short.
- **Family 3:** base block at world x ≤ +3 cm (same calibration issue).

## Before a session

- Restart any grasp/detect node whose file changed since it was launched (`lang_color_grasp.py` homes on
  start). A running node keeps the old code.
- Direct skill trials, no planner/critic, for tuning a placement skill:
  ```bash
  python3 verify2act/skill_test.py --top green --base red --trials 5                     # stacking
  python3 verify2act/skill_test.py --top red --base blue --relation left_of --trials 5   # rearrangement
  rosparam set /lang_color_grasp/place_gap 0.08   # if the opening jaws knock the reference block
  ```

## Ablations (optional, per task)

| flag | exercises |
|---|---|
| `--simulate_reprompt` | first VLM plan is flawed (bin: wrong block set; rearrangement: wrong side; stacking: blocks swapped) → goal-head reject → reflect |
| `--simulate_temporal_inconsistency` | first imagined transition is wrong → temporal-head reject → requery |
| `--simulate_uncertainty` | critic reports high uncertainty once → requery |
| `--exec_mode step_by_step` | execute one horizon, re-observe, re-plan |

## Metrics (from `summary.md`)

Real success rate (overall and among verified plans), verified rate, critic precision / false accepts,
replans, VLM calls, requeries, temporal / goal rejections, mean episode time.
