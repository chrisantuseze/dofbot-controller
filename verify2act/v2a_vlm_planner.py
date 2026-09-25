#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify2act/v2a_vlm_planner.py
=============================
VLM planner module for Verify2Act.
Decomposes a high-level language goal into sequential subtasks (task horizons),
with reflection/reprompting support upon critic rejection.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from verify2act.v2a_goal import parse_goal, parse_relative, parse_stack
from verify2act.v2a_world_model import MIN_BLOCK_PIXELS, color_pixels

logger = logging.getLogger(__name__)

COLOR_CODE_MAP = {
    "red": 7,
    "green": 8,
    "blue": 9,
    "yellow": 10,
}


@dataclass
class Subtask:
    action_text: str
    color: str
    color_id: int
    target_placement: str
    kind: str = "pick_place"          # pick_place | stack | rearrange: each one complete pick-and-place
    base_color: Optional[str] = None  # stack: block to stack onto; rearrange: reference block


class VLMPlanner:
    """
    VLM Planner for decomposing language goals into executable subtask horizons.
    Supports deterministic multi-attempt simulation or live prompting.
    """

    def __init__(self, simulate_reprompt: bool = False):
        """
        simulate_reprompt: If True, Attempt 1 outputs a deliberately flawed plan
        (e.g., omitting a required color or swapping bins) to demonstrate
        critic rejection, reflection, and successful re-planning on Attempt 2.
        """
        self.simulate_reprompt = simulate_reprompt
        self._proposals = 0

    def propose(self, current_frame, language_goal: str, history: List[str] = None) -> List[Subtask]:
        """
        Stub of VLMPlanner.propose(): plan from the CURRENT observation + history of executed actions.
        Only blocks still visible on the table are planned, so re-planning after a partial or failed
        execution naturally continues from the real state (receding horizon).
        """
        history = history or []
        self._proposals += 1
        flawed = self.simulate_reprompt and self._proposals == 1
        logger.info(f"[VLM Planner] propose #{self._proposals} for '{language_goal}' (history={history})")

        # One horizon = one complete pick-and-place, so stacking and rearrangement are single subtasks.
        stack = parse_stack(language_goal)
        if stack:
            top, base = stack
            if flawed:   # classic ordering mistake: the base block moved onto the top one
                logger.info("[VLM Planner] (simulating a naive proposal: top and base swapped)")
                top, base = base, top
            return [Subtask(f"pick and place {top} block on {base} block", top, COLOR_CODE_MAP[top], "on_" + base,
                            kind="stack", base_color=base)]

        rel = parse_relative(language_goal)
        if rel:
            mover, relation, ref = rel
            if flawed:   # classic spatial mistake: the right blocks, the wrong side
                logger.info("[VLM Planner] (simulating a naive proposal: wrong side of the reference block)")
                relation = "right_of" if relation == "left_of" else "left_of"
            side = relation.split("_")[0]
            return [Subtask(f"pick and place {mover} block to the {side} of {ref} block", mover, COLOR_CODE_MAP[mover],
                            relation, kind="rearrange", base_color=ref)]

        move, keep = parse_goal(language_goal)
        if current_frame is not None:
            move = [c for c in move if color_pixels(current_frame, c) >= MIN_BLOCK_PIXELS]
        if flawed:
            logger.info("[VLM Planner] (simulating a naive proposal)")
            move = move + keep[:1] if keep else move[:-1]
        return [self._create_subtask(f"pick and place {c} block into the bin", c, "left_bin") for c in move]

    def reflect(self, current_frame, language_goal: str, history: List[str], old_plan: List[Subtask], ctx: dict) -> List[Subtask]:
        """
        Stub of VLMPlanner.reflect(): a real VLM receives the images plus the critic's diagnosis in `ctx`
        and returns a revised plan.  The stub logs the diagnosis and re-plans without the simulated flaw.
        """
        logger.info(f"[VLM Planner] reflect on critic feedback: {ctx.get('reason')} (failed step: {ctx.get('failed_step')})")
        return self.propose(current_frame, language_goal, history)

    def _create_subtask(self, text: str, color: str, target: str) -> Subtask:
        cid = COLOR_CODE_MAP.get(color, 7)
        return Subtask(
            action_text=text,
            color=color,
            color_id=cid,
            target_placement=target,
        )
