#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify2act/v2a_world_model.py
=============================
World Model interface and stub for the Verify2Act framework.

Takes the current scene image S_t and a subtask action A_t, and imagines the
consequence scene S_{t+1} for the next horizon.
"""

import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2
import numpy as np

from verify2act.v2a_goal import parse_relative, parse_step

logger = logging.getLogger(__name__)

# Canonical color definitions (BGR)
COLOR_BGR = {
    "red": (30, 30, 220),
    "green": (40, 200, 40),
    "blue": (220, 100, 30),
    "yellow": (30, 210, 220),
}

BANNER_H = 34   # top strip used for overlay text; ignored by colour analysis
MIN_BLOCK_PIXELS = 300   # pixels of one colour needed to say "that block is visible"
COLOR_DIR = Path(__file__).resolve().parent.parent / "dofbot_pro_ws" / "src" / "dofbot_pro_voice_ctrl" / "scripts" / "Color"


def parse_action(action_text: str) -> Tuple[str, str]:
    """Extract (color, destination) from e.g. 'pick and place red block into the bin'."""
    text = action_text.lower()
    return next((c for c in COLOR_BGR if c in text), "red"), "left_bin"


def color_mask(frame: np.ndarray, color: str) -> np.ndarray:
    """Binary mask of `color` pixels: exact stub-rendered BGR OR the robot's calibrated HSV range."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    dist = np.linalg.norm(frame.astype(np.int16) - np.array(COLOR_BGR[color], np.int16), axis=2)
    mask = (dist < 40).astype(np.uint8) * 255
    v = None
    try:
        v = [int(float(t)) for t in (COLOR_DIR / f"{color}_colorHSV.text").read_text().replace("\n", ",").split(",") if t.strip()]
        mask |= cv2.inRange(hsv, tuple(v[:3]), tuple(v[3:6]))
    except Exception:
        v = None
    if color == "red":
        # Red wraps the hue circle, so the calibrated 160-180 range alone catches only part of the block.
        # Mirror lang_color_detect._find_blob exactly: the 0-8 band reuses the calibrated S/V floors
        # (hue <= 8, not 10, keeps the wooden table at hue 9-14 out).  Without this the stub's red mask
        # covered ~26% of the red block where the detector covered 64%, so the critic and the robot
        # disagreed about the red block while every other colour matched.
        if v:
            mask |= cv2.inRange(hsv, (0, v[1], v[2]), (8, v[4], v[5]))
        # Shaded red (e.g. under a stacked block) drops below the calibrated V floor entirely.
        mask |= cv2.inRange(hsv, (0, 190, 30), (8, 255, 110))
    mask[:BANNER_H] = 0
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))


def blob_bbox(frame: np.ndarray, color: str):
    """Largest blob of `color`: (x, y, w, h, mask_crop) or None."""
    # closing merges fragments of one block (lighting splits a block's faces into separate blobs)
    mask = cv2.morphologyEx(color_mask(frame, color), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if n < 2:
        return None
    b = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[b, cv2.CC_STAT_AREA] < MIN_BLOCK_PIXELS:
        return None
    x, y, w, h = (int(stats[b, k]) for k in (cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP, cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT))
    return x, y, w, h, (labels[y:y + h, x:x + w] == b).astype(np.uint8)


def color_pixels(frame: np.ndarray, color: str) -> int:
    return int(np.count_nonzero(color_mask(frame, color)))


@dataclass
class WorldModelRollout:
    imagined_frame: np.ndarray
    action_text: str
    target_color: str
    target_location: str
    injected_fault: str = ""   # logging only -- the critic must judge from pixels, never read this


class WorldModelStub:
    """
    Simulated World Model for tabletop pick-and-place manipulation.
    Produces imagined next-horizon frames S_{t+1} given S_t and A_t.
    """

    def __init__(self, debug_dir: Optional[str] = None):
        self.debug_dir = debug_dir
        self._held = None   # (color, crop_bgr, crop_mask) of the block imagined to be in the gripper

    def create_synthetic_scene(self, present_colors=("green", "blue", "yellow")) -> np.ndarray:
        """Offline stand-in for the camera view: white sheet on a wooden table with blocks."""
        img = np.full((480, 640, 3), (40, 70, 120), dtype=np.uint8)
        cv2.rectangle(img, (150, 20), (560, 480), (235, 235, 230), -1)
        cv2.arrowedLine(img, (140, 240), (20, 240), (200, 200, 200), 3, tipLength=0.3)
        cv2.putText(img, "BIN", (40, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        spots = {"red": (230, 330), "green": (200, 190), "blue": (390, 250), "yellow": (510, 210)}
        for color in present_colors:
            x, y = spots[color]
            cv2.rectangle(img, (x - 45, y - 60), (x + 45, y + 60), COLOR_BGR[color], -1)
        return img

    def parse_action(self, action_text: str) -> Tuple[str, str]:
        return parse_action(action_text)

    def _erase_block(self, frame: np.ndarray, color: str) -> bool:
        """Remove the `color` block by inpainting its bounding box (repeated until no blob is left)."""
        erased = False
        for _ in range(3):
            bb = blob_bbox(frame, color)
            if bb is None:
                break
            x, y, w, h, _m = bb
            m = max(8, int(0.2 * min(w, h)))   # margin also swallows the tag / shadow next to the block
            box = np.zeros(frame.shape[:2], np.uint8)
            # A block cut off by the banner strip (masked out above BANNER_H) continues to the frame edge: erase up
            # to row 0, or inpainting refills the box from the red still above it (seen: 707 px left of a picked
            # red block at the top of the frame).
            top = 0 if y <= BANNER_H + 1 else y - m
            box[top:y + h + m, max(0, x - m):x + w + m] = 255
            frame[:] = cv2.inpaint(frame, box, 7, cv2.INPAINT_TELEA)
            erased = True
        return erased

    def reset(self, session: str = "") -> None:
        self._held = None

    def _remember_block(self, frame: np.ndarray, color: str) -> None:
        """Cut the block out of the frame so a later place_on can render it elsewhere."""
        bb = blob_bbox(frame, color)
        if bb:
            x, y, w, h, m = bb
            self._held = (color, frame[y:y + h, x:x + w].copy(), m)

    def _imagine_place_on(self, cur: np.ndarray, out: np.ndarray, color: str, base: str, fault_mode: bool,
                          relation: Optional[str] = None) -> str:
        """Paste the held block on top of the base block (or, as a fault, in empty space beside it).
        relation 'left_of' / 'right_of' (place_at): paste it next to the base block instead, ~2 block widths
        centre to centre (the robot's default ~place_gap); as a fault, on the opposite side."""
        if self._held is None or self._held[0] != color:
            # Nothing was picked first: a real WM would hallucinate here; the stub leaves the scene unchanged
            # so the critic can flag the ordering violation.
            return f"no held {color} block to place"
        bb = blob_bbox(cur, base)
        if bb is None:
            return f"base {base} block not visible"
        bx, by, bw, bh, _ = bb
        _, crop, mask = self._held
        ch, cw = mask.shape
        cx, cy = bx + bw // 2, by + bh // 2 - int(0.15 * bh)      # slightly raised = sitting on top
        fault = ""
        if relation:
            side = -1 if relation == "left_of" else 1
            if fault_mode:
                side = -side
                fault = f"injected: {color} block placed on the wrong side of {base}"
            cx, cy = bx + bw // 2 + side * 2 * bw, by + bh // 2
        elif fault_mode:
            cx += bw + cw // 2 + 10                                # lands beside, not on, the base
            fault = f"injected: {color} block placed beside {base} instead of on it"
        x0, y0 = int(np.clip(cx - cw // 2, 0, 640 - cw)), int(np.clip(cy - ch // 2, BANNER_H, 480 - ch))
        roi = out[y0:y0 + ch, x0:x0 + cw]
        roi[mask.astype(bool)] = crop[mask.astype(bool)]
        return fault

    def imagine(
        self,
        current_frame: np.ndarray,
        action_text: str,
        simulate_inconsistency: bool = False,
    ) -> WorldModelRollout:
        """
        S_t + A_t -> S_{t+1}: the picked block leaves the table (into the off-camera bin).
        With simulate_inconsistency a DIFFERENT block is removed -- a fault that only
        shows up in pixels, which the critic has to detect visually.
        """
        kind, color, base = parse_step(action_text)
        dest = {"pick_place": "left_bin", "pick": "hold", "place_on": f"on_{base}"}.get(kind)
        next_frame = current_frame.copy()

        fault = ""
        if kind == "place_on":
            fault = self._imagine_place_on(current_frame, next_frame, color, base, simulate_inconsistency)
        elif kind == "place_at":
            relation = (parse_relative(action_text) or (None, "left_of", None))[1]
            dest = f"{relation}_{base}"
            fault = self._imagine_place_on(current_frame, next_frame, color, base, simulate_inconsistency, relation)
        else:
            if kind == "pick":
                self._remember_block(current_frame, color)
            target = color
            if simulate_inconsistency:
                wrong = next((c for c in COLOR_BGR if c != color and color_pixels(current_frame, c) >= MIN_BLOCK_PIXELS), None)
                fault = f"injected: removed {wrong} block instead of {color}"
                target = wrong
            if target:
                self._erase_block(next_frame, target)

        cv2.rectangle(next_frame, (0, 0), (640, BANNER_H - 2), (25, 25, 30), -1)
        cv2.putText(next_frame, f"[WM Imagined] {action_text}", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 220, 120), 1)

        return WorldModelRollout(next_frame, action_text, color, dest, injected_fault=fault)
