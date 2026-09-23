#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify2act/v2a_critic.py
========================
Critic model for the Verify2Act framework with dual heads:
1. Temporal Consistency Head: Checks pairwise transition (S_t, S_{t+1}) given subtask A_t.
2. Goal Head: Checks final imagined scene S_H against the high-level language goal.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from verify2act.v2a_goal import COLORS, parse_goal, parse_relative, parse_stack, parse_step
from verify2act.v2a_world_model import MIN_BLOCK_PIXELS, blob_bbox, color_pixels

logger = logging.getLogger(__name__)


@dataclass
class CriticVerdict:
    accepted: bool
    score: float
    reason: str
    head: str  # "temporal_consistency" or "goal"


KEEP_FRACTION = 0.7   # a block that must stay put keeps at least this share of its pixels


class CriticModel:
    """
    Stub critic with a Temporal Consistency Head and a Goal Head.  Both judge the
    IMAGES (colour-blob pixel counts), never metadata from the world model, so they
    behave like a learned critic would.  "Block is in the bin" == "block left the
    table", because the bin is off-camera.
    """

    BASE_STD = 0.03   # typical MC std of the real critic is 0.03-0.065 (confidence_threshold = 0.08)

    def __init__(self, temporal_threshold: float = 0.5, goal_threshold: float = 0.6, force_uncertain: int = 0):
        self.temporal_threshold = temporal_threshold   # theta_c
        self.goal_threshold = goal_threshold           # theta_p
        self._force_uncertain = force_uncertain        # next N estimates report high uncertainty (exercises "requery")

    # ── Interface of the research critic (DINOv2DualHeadCritic): (mean similarity, MC std) ──
    # A real critic embeds DINO features and returns cosine similarities; this stub derives the
    # score from colour-blob checks.  Swap this class for the real critic to run on the GPU box.

    def _std(self) -> float:
        if self._force_uncertain > 0:
            self._force_uncertain -= 1
            return 0.12
        return self.BASE_STD

    def temporal_sim_with_uncertainty(self, current_frame, next_frame, action_text):
        v = self.temporal_consistency_head(current_frame, next_frame, action_text)
        return v.score, self._std(), v.reason

    def goal_sim_with_uncertainty(self, frame, language_goal, initial_frame=None, executed=None):
        v = self.goal_head(frame, language_goal, executed or [], initial_frame=initial_frame)
        return v.score, self._std(), v.reason

    @staticmethod
    def _stacked(frame: np.ndarray, top: str, base: str, base_ref: np.ndarray) -> bool:
        """`top` is visible and its blob centre lies inside the base block's (reference) footprint."""
        t, b = blob_bbox(frame, top), blob_bbox(base_ref, base)
        if t is None or b is None:
            return False
        tx, ty = t[0] + t[2] / 2, t[1] + t[3] / 2
        bx, by, bw, bh, _ = b
        return bx - 0.1 * bw <= tx <= bx + 1.1 * bw and by - 0.1 * bh <= ty <= by + 1.1 * bh

    @staticmethod
    def _beside(frame: np.ndarray, mover: str, ref: str, relation: str) -> Tuple[bool, str]:
        """`mover` sits on the `relation` side of `ref`, next to it: centre-to-centre between 0.6 and 3.5 ref-block
        widths along x (clear of the ref block but not across the sheet) and within one block height in y."""
        m, r = blob_bbox(frame, mover), blob_bbox(frame, ref)
        if m is None or r is None:
            return False, f"{mover if m is None else ref} block not visible"
        mx, my = m[0] + m[2] / 2, m[1] + m[3] / 2
        rx, ry, rw, rh = r[0] + r[2] / 2, r[1] + r[3] / 2, r[2], r[3]
        dx = (rx - mx) if relation == "left_of" else (mx - rx)
        side = relation.split("_")[0]
        if dx < 0.6 * rw:
            return False, f"{mover} block is not to the {side} of the {ref} block (dx={dx:.0f} px, ref w={rw} px)"
        if dx > 3.5 * rw:
            return False, f"{mover} block is too far from the {ref} block (dx={dx:.0f} px, ref w={rw} px)"
        if abs(my - ry) > rh:
            return False, f"{mover} block is not level with the {ref} block (dy={my - ry:.0f} px, ref h={rh} px)"
        return True, ""

    def temporal_consistency_head(
        self,
        current_frame: np.ndarray,
        next_frame: np.ndarray,
        subtask_text: str,
        rollout_info: Optional[object] = None,   # accepted for API compat; deliberately unused
    ) -> CriticVerdict:
        """Does S_{t+1} show exactly what `subtask_text` should do to S_t?"""
        kind, color, base = parse_step(subtask_text)
        problems = []

        before, after = color_pixels(current_frame, color), color_pixels(next_frame, color)
        # "Held block still on the table" = a block-sized blob, not a raw pixel count: the wooden table's grain
        # passes the red mask as scattered specks (~350 px on the 2026-09-24 task2a frame, > MIN_BLOCK_PIXELS),
        # which made every "place red ..." step look like red had never been picked up.
        still_on_table = blob_bbox(current_frame, color) is not None
        if kind in ("pick", "pick_place"):
            if before < MIN_BLOCK_PIXELS:
                problems.append(f"no {color} block visible in the current scene")
            elif after > 0.3 * before:
                problems.append(f"{color} block still on the table after '{subtask_text}'")
        elif kind == "place_at":
            relation = (parse_relative(subtask_text) or (None, "left_of", None))[1]
            if still_on_table:
                problems.append(f"ordering violation: {color} block was never picked up (still on the table)")
            else:
                ok, why = self._beside(next_frame, color, base, relation)
                if not ok:
                    problems.append(why)
            b, a = color_pixels(current_frame, base), color_pixels(next_frame, base)
            if b < MIN_BLOCK_PIXELS:
                problems.append(f"reference {base} block not visible")
            elif a < KEEP_FRACTION * b:
                problems.append(f"reference {base} block changed ({b} -> {a} px)")
        else:  # place_on
            if still_on_table:
                problems.append(f"ordering violation: {color} block was never picked up (still on the table)")
            elif not self._stacked(next_frame, color, base, current_frame):
                problems.append(f"{color} block is not resting on the {base} block")
            if color_pixels(current_frame, base) < MIN_BLOCK_PIXELS:
                problems.append(f"base {base} block not visible")

        for other in COLORS:
            if other in (color, base):
                continue
            b, a = color_pixels(current_frame, other), color_pixels(next_frame, other)
            if b >= MIN_BLOCK_PIXELS and a < KEEP_FRACTION * b:
                # areas logged: this rejection fired once on a real frame (2026-09-23) and could not be
                # reproduced in 25 runs; without the numbers the cause is unrecoverable from the logs.
                problems.append(f"unrelated {other} block changed ({b} -> {a} px)")

        if problems:
            score = max(0.05, 0.45 - 0.2 * (len(problems) - 1))   # below theta_c (0.5)
            reason = "Temporal violation: " + "; ".join(problems) + "."
            logger.warning("[Critic:Temporal] REJECT (score=%.2f): %s", score, reason)
            return CriticVerdict(False, score, reason, "temporal_consistency")

        reason = {"pick": f"{color} block lifted off the table, other blocks unchanged.",
                  "place_on": f"{color} block now rests on the {base} block, other blocks unchanged.",
                  "place_at": f"{color} block placed beside the {base} block, other blocks unchanged."}.get(
                      kind, f"{color} block removed from table, other blocks unchanged.")
        reason = "Temporal transition consistent: " + reason
        logger.info("[Critic:Temporal] ACCEPT")
        return CriticVerdict(True, 0.94, reason, "temporal_consistency")

    def goal_head(
        self,
        final_frame: np.ndarray,
        language_goal: str,
        executed_subtasks: List[str],
        initial_frame: Optional[np.ndarray] = None,
    ) -> CriticVerdict:
        """Does the final imagined scene S_H satisfy the language goal, judged against S_0?"""
        if initial_frame is None:
            initial_frame = final_frame
        stack = parse_stack(language_goal)
        if stack:
            return self._stack_goal(final_frame, initial_frame, *stack)
        rel = parse_relative(language_goal)
        if rel:
            return self._relative_goal(final_frame, initial_frame, *rel)
        move, keep = parse_goal(language_goal)
        # Anything not named in the goal must also be left alone.
        keep = keep + [c for c in COLORS if c not in move and c not in keep
                       and color_pixels(initial_frame, c) >= MIN_BLOCK_PIXELS]
        if not move:
            return CriticVerdict(False, 0.10, "Goal head could not parse any target block from the goal.", "goal")

        problems = []
        for c in move:
            if color_pixels(initial_frame, c) < MIN_BLOCK_PIXELS:
                problems.append(f"{c} block was never visible in the scene")
            elif color_pixels(final_frame, c) >= MIN_BLOCK_PIXELS:
                problems.append(f"{c} block still on the table")
        for c in keep:
            b = color_pixels(initial_frame, c)
            if b >= MIN_BLOCK_PIXELS and color_pixels(final_frame, c) < KEEP_FRACTION * b:
                problems.append(f"{c} block was moved but should stay")

        total = len(move) + len(keep)
        if not problems:
            return CriticVerdict(True, 0.95, f"Goal satisfied: {', '.join(move)} moved to bin, "
                                 f"{', '.join(keep) or 'no other block'} untouched.", "goal")
        score = float(max(0.05, 1.0 - len(problems) / max(total, 1)))
        return CriticVerdict(False, min(score, 0.4), "Goal not satisfied: " + "; ".join(problems) + ".", "goal")

    def _stack_goal(self, final: np.ndarray, initial: np.ndarray, top: str, base: str) -> CriticVerdict:
        problems = []
        if color_pixels(initial, top) < MIN_BLOCK_PIXELS or color_pixels(initial, base) < MIN_BLOCK_PIXELS:
            problems.append("both blocks must be visible in the initial scene")
        else:
            if not self._stacked(final, top, base, initial):
                problems.append(f"{top} block is not on top of the {base} block")
        for c in COLORS:
            if c in (top, base):
                continue
            b = color_pixels(initial, c)
            if b >= MIN_BLOCK_PIXELS and color_pixels(final, c) < KEEP_FRACTION * b:
                problems.append(f"{c} block was moved but should stay")
        if not problems:
            return CriticVerdict(True, 0.95, f"Goal satisfied: {top} block stacked on the {base} block.", "goal")
        return CriticVerdict(False, 0.3, "Goal not satisfied: " + "; ".join(problems) + ".", "goal")

    def _relative_goal(self, final: np.ndarray, initial: np.ndarray, mover: str, relation: str, ref: str) -> CriticVerdict:
        problems = []
        if color_pixels(initial, mover) < MIN_BLOCK_PIXELS or color_pixels(initial, ref) < MIN_BLOCK_PIXELS:
            problems.append("both blocks must be visible in the initial scene")
        else:
            ok, why = self._beside(final, mover, ref, relation)
            if not ok:
                problems.append(why)
        for c in COLORS:   # the reference block included: it must not have been pushed
            if c == mover:
                continue
            b = color_pixels(initial, c)
            if b >= MIN_BLOCK_PIXELS and color_pixels(final, c) < KEEP_FRACTION * b:
                problems.append(f"{c} block was moved but should stay")
        if not problems:
            return CriticVerdict(True, 0.95, f"Goal satisfied: {mover} block is to the "
                                 f"{relation.split('_')[0]} of the {ref} block.", "goal")
        return CriticVerdict(False, 0.3, "Goal not satisfied: " + "; ".join(problems) + ".", "goal")
