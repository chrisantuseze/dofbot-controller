# Plan server: subtask vocabulary change (one horizon = one pick-and-place)

Written 2026-09-25 on the Jetson for the Claude session that works on the **lab PC** in `chrisantuseze/verify2act`
(branch `main-wm`, `verify2act/robot/`). It is the reverse of `CLIENT_INTEGRATION.md`. The Jetson side is already done
in `dofbot-controller` (see "Jetson side" at the end). The server has to change to match, or the Jetson will refuse every
family-2/3 plan as `invalid_steps` / outside the vocabulary.

---

## 1. Why

A subtask is the unit the world model imagines and the critic scores (`expand_subtask_plan`: one subtask = one imagination
step), and it is the point where the Jetson re-observes and calls `plan` again. The arm **cannot hold a block through
that pause**. A `plan` call takes 20–60 s, sometimes minutes, and a loaded arm stalls joints 2/3. In any case, the grasp
skills are built to run pick → place back to back. A mid-grasp frame (block in the gripper, eye-in-hand camera) is also a
poor state for the WM to imagine and for the critic to score.

So **every subtask is one complete manipulation that starts and ends with nothing held**:

| goal family | old plan (2 horizons) | new plan (1 horizon) |
|---|---|---|
| bin clearing | `pick and place <c> block into the bin` (per block) | unchanged |
| rearrangement | `pick <c> block`, `place <c> block to the left of <b> block` | `pick and place <c> block to the left of <b> block` |
| stacking | `pick <c> block`, `place <c> block on <b> block` | `pick and place <c> block on <b> block` |

The Jetson turns each of the new subtasks into `locate <b>` → `pick <c>` → `place_on|place_at` with no pause in between.

## 2. The new vocabulary (exact strings)

`<c>`, `<b>` ∈ red, green, blue, yellow, and `<c>` ≠ `<b>`. Plus `done`.

```
pick and place <c> block into the bin
pick and place <c> block on <b> block
pick and place <c> block to the left of <b> block
pick and place <c> block to the right of <b> block
```

`pick <c> block` and `place <c> block ...` are **retired**. The Jetson rejects them.

## 3. Server changes

### 3.1 `verify2act/robot/prompts.py`

```python
# The subtask vocabulary the Jetson skills execute (dofbot-controller verify2act/remote/planner_client.py).
# One subtask = one WM horizon = one complete pick-and-place that ends with nothing held.
SUBTASK_PATTERNS = (
    re.compile(rf"^pick and place {_C} block into the bin$"),
    re.compile(rf"^pick and place {_C} block on {_C} block$"),
    re.compile(rf"^pick and place {_C} block to the (left|right) of {_C} block$"),
)
DONE = "done"

SUBTASK_TEMPLATES = (
    "pick and place <c> block into the bin",
    "pick and place <c> block on <b> block",
    "pick and place <c> block to the left of <b> block",
    "pick and place <c> block to the right of <b> block",
)
```

Also recommended: make `is_valid_subtask` reject `<c>` == `<b>` (e.g. `pick and place red block on red block`). The Jetson
already refuses those.

### 3.2 `verify2act/configs/prompts/dofbot/system/propose.yaml`

Replace the "Subtasks" list and goal types 2 and 3, and delete the "Only one block can be held at a time" bullet:

```
  Subtasks (use exactly this wording; <c> and <b> are block colours, <c> different from <b>). Each subtask is one
  complete grasp-and-release: the robot never holds a block between subtasks.
    - "pick and place <c> block into the bin"               grasp block <c> and drop it into the bin
    - "pick and place <c> block on <b> block"               grasp block <c> and put it on top of block <b>
    - "pick and place <c> block to the left of <b> block"   grasp block <c> and put it beside block <b>, on its left
    - "pick and place <c> block to the right of <b> block"  grasp block <c> and put it beside block <b>, on its right

  Goal types and how to plan them:
    1. Bin clearing: (unchanged)
    2. Rearrangement, e.g. "Put the yellow block to the right of the green block":
       exactly ["pick and place <c> block to the <left|right> of <b> block"], where <c> is the block being moved
       and <b> the reference block, which stays where it is.
    3. Stacking, e.g. "Stack the red block on top of the green block":
       exactly ["pick and place <c> block on <b> block"], where <c> is the top block and <b> the base.
```

### 3.3 `verify2act/configs/prompts/dofbot/system/reflect.yaml`

```
  Allowed subtasks (exact wording):
    "pick and place <c> block into the bin", "pick and place <c> block on <b> block",
    "pick and place <c> block to the left of <b> block", "pick and place <c> block to the right of <b> block"

  Check the plan against the goal:
    - Bin clearing: (unchanged)
    - Rearrangement: ["pick and place <c> block to the <side> of <b> block"]: right block moved, right reference,
      right side.
    - Stacking: ["pick and place <c> block on <b> block"]: top and base not swapped.
    - Never repeat completed history entries.
```

Delete the bullet "If the last executed subtask is "pick <c> block", plan only the matching place."

### 3.4 `verify2act/robot/backend.py`

The warm-up at line ~162 evaluates `plan=["pick red block"]`. Change it to a string that is still in the vocabulary,
e.g. `["pick and place red block into the bin"]`.

### 3.5 `verify2act/robot/test_robot_server.py`

- `test_subtask_vocabulary`: the valid list becomes the four strings of §2 plus `done`. Add `"pick red block"`,
  `"place red block on blue block"` and `"pick and place red block on red block"` to the invalid list. For the
  `step_text` case, use e.g. `{"label": " Pick and place Red Block into the bin. "}`.
- `test_prompt_messages_build`: the asserted system-prompt phrases become
  `'["pick and place <c> block to the <left|right> of <b> block"]'` and `'["pick and place <c> block on <b> block"]'`.
- `EVAL_TASK_PLANS`:
  ```python
  "Put the red block to the left of the blue block": ["pick and place red block to the left of blue block"],
  "Put the green block to the right of the yellow block": ["pick and place green block to the right of yellow block"],
  "Stack the blue block on top of the yellow block": ["pick and place blue block on yellow block"],
  ```

### 3.6 `verify2act/robot/CLIENT_INTEGRATION.md`

Update §4 (the vocabulary table) and §7 step 5 (family 2 is now one subtask). The Jetson's copy of this file already has the new
text.

## 4. Things to check on the model side

- **World model conditioning.** The WM action text for a family-2/3 horizon is now the compound string, and one imagined
  step has to take the scene from "block on the table" to "block placed next to / on the base". The action encoder should
  handle this, since bin clearing already works the same way. Still, look at the first few imagined frames in
  `imagination_logs/` for a rearrangement goal.
- **Real-robot training data.** `transitions.jsonl` from the 09-24 family-2 sessions has the old two-step labels
  (`pick <c> block` then `place <c> block to the ... of <b> block`, as consecutive rows with the same `episode_id`). To reuse
  them in the new vocabulary, merge each pair into one transition: `image_t` of the pick row, `image_t1` of the place row,
  and `action_text` = the compound string. From now on the Jetson logs one transition per compound subtask.
- `horizon` (default 4) and the replan budget are unchanged. Family 2/3 plans are now length 1.

## 5. Verify

1. `pytest verify2act/robot/test_robot_server.py`
2. Restart the server. From the Jetson, `--dry_run --plan_server --task task2a` should return
   `plan == ["pick and place red block to the left of blue block"]` and `invalid_steps == []`.
3. The same for task3a (`pick and place blue block on yellow block`). Task 1a is unaffected.

## Jetson side (done, `dofbot-controller`)

- `verify2act/v2a_goal.py::parse_step`: kinds are `pick_place | stack | rearrange`.
- `verify2act/remote/planner_client.py`: validator = the four patterns of §2. It rejects same-colour base.
- `verify2act/v2a_pipeline.py::_run_skill`: `stack` / `rearrange` → `locate` → `pick` → `place_on|place_at`, back to back.
  One transition is logged per subtask.
- Stub planner / world model / critic: they emit, imagine and score the compound subtasks, so the offline path matches.
