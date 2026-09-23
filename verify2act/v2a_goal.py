#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify2act/v2a_goal.py
======================
Shared language-goal parsing for the planner stub and the critic stub.

Physical setup: coloured blocks on the sheet, ONE bin off-camera to the robot's left.
A goal names blocks to move into the bin and (optionally) blocks to leave alone.
    "Put the blue block and the yellow block into the bin"          -> move {blue, yellow}
    "Clear all cool-colored blocks into the bin, leave the yellow"  -> move {green, blue}, keep {yellow}
"""

import re
from typing import List, Tuple

COLORS = ["red", "green", "blue", "yellow"]
GROUPS = {"warm": ["red", "yellow"], "cool": ["green", "blue"]}
_KEEP_SPLIT = re.compile(r"\b(leave|except|but not|without touching|keep|don't touch|do not touch)\b")


def _colors_in(text: str) -> List[str]:
    hits = [(m.start(), c) for c in COLORS for m in re.finditer(rf"\b{c}\b", text)]
    for g, members in GROUPS.items():
        hits += [(m.start(), c) for m in re.finditer(rf"\b{g}\b", text) for c in members]
    ordered: List[str] = []
    for _, c in sorted(hits):
        if c not in ordered:
            ordered.append(c)
    return ordered


def parse_goal(goal: str) -> Tuple[List[str], List[str]]:
    """Return (colors_to_move_in_order, colors_to_leave)."""
    parts = _KEEP_SPLIT.split(goal.lower(), maxsplit=1)
    move = _colors_in(parts[0])
    keep = [c for c in _colors_in(parts[2]) if c not in move] if len(parts) == 3 else []
    return move, keep


_STACK = re.compile(r"\bstack\b.*?\b(red|green|blue|yellow)\b.*?\b(?:on|onto|on top of|atop)\b.*?\b(red|green|blue|yellow)\b")


def parse_stack(goal: str):
    """'Stack the blue block on top of the yellow block' -> ('blue', 'yellow') (top, base); else None."""
    m = _STACK.search(goal.lower())
    return (m.group(1), m.group(2)) if m and m.group(1) != m.group(2) else None


# Rearrangement: "Put the red block to the left of the blue block".  Left / right are image (= world x) directions;
# front / behind are not supported until the image-y <-> world-y direction has been checked on the robot.
_RELATIVE = re.compile(r"\b(red|green|blue|yellow)\b.*?\b(?:to the )?(left|right)\s+(?:side\s+)?of\b.*?\b(red|green|blue|yellow)\b")


def parse_relative(text: str):
    """'Put the red block to the left of the blue block' -> ('red', 'left_of', 'blue') (mover, relation, reference)."""
    m = _RELATIVE.search(text.lower())
    return (m.group(1), m.group(2) + "_of", m.group(3)) if m and m.group(1) != m.group(3) else None


_PLACE_ON = re.compile(r"\bplace\b.*?\b(red|green|blue|yellow)\b.*?\b(?:on|onto|on top of)\b.*?\b(red|green|blue|yellow)\b")


def parse_step(action_text: str):
    """Classify a subtask string -> (kind, color, base_color|None); kind in pick | place_on | place_at | pick_place.
    place_at: base_color is the reference block; the side comes from parse_relative()."""
    t = action_text.lower()
    color = next((c for c in COLORS if c in t), "red")
    rel = parse_relative(t)
    if rel and "place" in t:
        return "place_at", rel[0], rel[2]
    m = _PLACE_ON.search(t)
    if m:
        return "place_on", m.group(1), m.group(2)
    if "place" not in t:
        return "pick", color, None
    return "pick_place", color, None
