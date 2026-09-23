#!/usr/bin/env python3
"""
verify2act/vlm_critic.py
========================
GPT-4o Vision-Language Model Critic for Verify2Act.

Supports two modes controlled by the ``mock`` constructor flag:

  MOCK mode  (default, mock=True)
    Returns pre-scripted, deterministic responses keyed by attempt index.
    Attempt 1  -> REJECT  (path blocked by obstacle cubes)
    Attempt 2  -> ACCEPT  (obstacle-clearance plan)
    Zero network dependency — safe for live demos.

  LIVE mode  (mock=False)
    Sends the live camera frame to GPT-4o via the OpenAI API and parses the
    JSON response.  Requires OPENAI_API_KEY in environment.

Usage (standalone test):
    python3 verify2act/vlm_critic.py --test_image /path/to/frame.png
    python3 verify2act/vlm_critic.py --live --test_image /path/to/frame.png
"""

import base64
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── Scripted mock responses ───────────────────────────────────────────────────
# Edit these to match your exact demo narrative.
# Keys are 1-indexed attempt numbers (1 = first attempt, 2 = second, …).

SCRIPTED_RESPONSES: Dict[int, Dict] = {
    1: {
        "proposal": {
            "reasoning": (
                "I can see a red cube on the table. "
                "There appear to be other cubes in the workspace. "
                "The direct approach is to grasp the red cube."
            ),
            "plan": [
                "Move arm above red cube",
                "Descend to grasp height",
                "Close gripper on red cube",
                "Lift red cube",
                "Move to target zone",
                "Release cube",
            ],
        },
        "verdict": {
            "status": "REJECT",
            "score": 0.19,
            "reason": (
                "The blue and green obstacle cubes are placed directly in front of the "
                "red target cube, blocking the gripper's approach path. Executing the "
                "plan as-is would result in a collision with the blockers before the "
                "gripper can reach the red cube."
            ),
            "reflected_plan": [
                "Move blue cube to left clear zone",
                "Move green cube to right clear zone",
                "Move arm above red cube (now unobstructed)",
                "Descend to grasp height",
                "Close gripper on red cube",
                "Lift red cube",
                "Move to target zone",
                "Release cube",
            ],
        },
    },
    2: {
        "proposal": {
            "reasoning": (
                "After reflecting on the previous failure, I recognise that the red cube "
                "is blocked by blue and green obstacle cubes. I will first clear the "
                "obstacles, then grasp the target."
            ),
            "plan": [
                "Move blue cube to left clear zone",
                "Move green cube to right clear zone",
                "Move arm above red cube (now unobstructed)",
                "Descend to grasp height",
                "Close gripper on red cube",
                "Lift red cube",
                "Move to target zone",
                "Release cube",
            ],
        },
        "verdict": {
            "status": "ACCEPT",
            "score": 0.91,
            "reason": (
                "The reflected plan correctly clears both obstacle cubes before "
                "approaching the target. The path to the red cube is now unobstructed "
                "and the plan is executable."
            ),
            "reflected_plan": [],
        },
    },
}

# Fallback for attempt numbers beyond what is scripted
_DEFAULT_ACCEPT: Dict = {
    "proposal": {
        "reasoning": "Scene appears clear. Proceeding with direct grasp.",
        "plan": ["Grasp target cube", "Place at target zone"],
    },
    "verdict": {
        "status": "ACCEPT",
        "score": 0.85,
        "reason": "Path is clear.",
        "reflected_plan": [],
    },
}


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class VLMPlan:
    """High-level action plan proposed by the VLM."""
    reasoning: str
    steps: List[str]
    attempt: int

    def pretty(self) -> str:
        lines = [f"  VLM Plan (Attempt {self.attempt}):"]
        for i, s in enumerate(self.steps, 1):
            lines.append(f"    Step {i}: {s}")
        return "\n".join(lines)


@dataclass
class CriticVerdict:
    """Critic evaluation of a proposed plan."""
    status: str          # "ACCEPT" or "REJECT"
    score: float         # 0.0 - 1.0
    reason: str
    reflected_plan: List[str] = field(default_factory=list)
    attempt: int = 1

    @property
    def accepted(self) -> bool:
        return self.status == "ACCEPT"

    def pretty(self) -> str:
        icon = "ACCEPT" if self.accepted else "REJECT"
        lines = [
            f"  Critic Verdict: {icon}  (score={self.score:.2f})",
            f"  Reason: {self.reason}",
        ]
        if self.reflected_plan:
            lines.append("  Reflected Plan:")
            for i, s in enumerate(self.reflected_plan, 1):
                lines.append(f"    Step {i}: {s}")
        return "\n".join(lines)


# ── VLM Critic ────────────────────────────────────────────────────────────────

class VLMCritic:
    """
    Verify2Act critic powered by GPT-4o vision.

    Args:
        mock:        If True (default), return scripted responses without any API call.
        api_key:     OpenAI API key.  Defaults to OPENAI_API_KEY env var.
        model:       OpenAI model name (default: gpt-4o).
        temperature: Sampling temperature for live calls (default: 0.2).
    """

    def __init__(
        self,
        mock: bool = True,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.2,
    ):
        self.mock        = mock
        self.model       = model
        self.temperature = temperature
        self._client     = None

        if not mock:
            key = api_key or os.environ.get("OPENAI_API_KEY", "")
            if not key:
                raise EnvironmentError(
                    "OPENAI_API_KEY is not set. "
                    "Export it or pass api_key= to VLMCritic()."
                )
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=key)
            except ImportError:
                raise ImportError(
                    "openai package not installed. Run: pip install openai"
                )
            logger.info("[VLMCritic] LIVE mode — using model %s", model)
        else:
            logger.info("[VLMCritic] MOCK mode — scripted responses active")

    # ── Public API ─────────────────────────────────────────────────────────────

    def propose(
        self,
        image: np.ndarray,
        task: str,
        attempt: int = 1,
    ) -> VLMPlan:
        """
        Given a camera frame and task description, propose a high-level action plan.

        Args:
            image:   BGR uint8 numpy array from OpenCV (may be None in mock mode).
            task:    Natural language task string, e.g. "pick and place red cube".
            attempt: 1-indexed attempt number (drives mock response selection).
        Returns:
            VLMPlan
        """
        logger.info("[VLMCritic] propose() attempt=%d task='%s'", attempt, task)

        if self.mock:
            resp = SCRIPTED_RESPONSES.get(attempt, _DEFAULT_ACCEPT)
            prop = resp["proposal"]
            plan = VLMPlan(
                reasoning=prop["reasoning"],
                steps=prop["plan"],
                attempt=attempt,
            )
            logger.info("[VLMCritic] (mock) plan steps=%d", len(plan.steps))
            return plan

        # ── Live GPT-4o call ───────────────────────────────────────────────
        b64 = self._encode_image(image)
        system_prompt = (
            "You are a robot manipulation planner for a 6-DoF desktop robot arm. "
            "Given a camera image of the robot's workspace, propose a minimal, "
            "ordered sequence of high-level manipulation sub-goals to complete the task. "
            "Be concise. Output ONLY valid JSON in this exact format:\n"
            '{"reasoning": "<one sentence>", "plan": ["step 1", "step 2", ...]}'
        )
        user_prompt = (
            f'Task: "{task}"\nAttempt: {attempt}\n'
            "Analyse the scene and propose a plan."
        )

        raw = self._call_api(system_prompt, user_prompt, b64)
        try:
            parsed = json.loads(raw)
            return VLMPlan(
                reasoning=parsed.get("reasoning", ""),
                steps=parsed.get("plan", []),
                attempt=attempt,
            )
        except json.JSONDecodeError:
            logger.warning("[VLMCritic] JSON parse failed for proposal; using raw text")
            return VLMPlan(reasoning=raw, steps=[raw], attempt=attempt)

    def verify(
        self,
        image: np.ndarray,
        plan: VLMPlan,
        attempt: int = 1,
    ) -> CriticVerdict:
        """
        Verify whether a proposed plan is executable given the current scene.

        Args:
            image:   BGR uint8 numpy array (may be None in mock mode).
            plan:    VLMPlan returned by propose().
            attempt: 1-indexed attempt number.
        Returns:
            CriticVerdict
        """
        logger.info("[VLMCritic] verify() attempt=%d", attempt)

        if self.mock:
            resp    = SCRIPTED_RESPONSES.get(attempt, _DEFAULT_ACCEPT)
            v       = resp["verdict"]
            verdict = CriticVerdict(
                status=v["status"],
                score=v["score"],
                reason=v["reason"],
                reflected_plan=v.get("reflected_plan", []),
                attempt=attempt,
            )
            logger.info("[VLMCritic] (mock) verdict=%s score=%.2f",
                        verdict.status, verdict.score)
            return verdict

        # ── Live GPT-4o call ───────────────────────────────────────────────
        b64 = self._encode_image(image)
        plan_text = "\n".join(
            f"  {i+1}. {s}" for i, s in enumerate(plan.steps)
        )
        system_prompt = (
            "You are a robot manipulation critic. "
            "Evaluate whether the proposed plan is physically executable given the "
            "camera image. Consider obstacles, object positions, and gripper "
            "accessibility. Output ONLY valid JSON:\n"
            '{"status": "ACCEPT" or "REJECT", "score": 0.0-1.0, '
            '"reason": "<one sentence>", "reflected_plan": ["step 1", ...]}'
            "\nIf ACCEPT, reflected_plan may be empty. "
            "If REJECT, reflected_plan must fix the blocking issue."
        )
        user_prompt = (
            f"Proposed plan:\n{plan_text}\n\n"
            "Is this plan executable? If not, provide a corrected plan."
        )

        raw = self._call_api(system_prompt, user_prompt, b64)
        try:
            parsed = json.loads(raw)
            return CriticVerdict(
                status=parsed.get("status", "REJECT"),
                score=float(parsed.get("score", 0.0)),
                reason=parsed.get("reason", ""),
                reflected_plan=parsed.get("reflected_plan", []),
                attempt=attempt,
            )
        except json.JSONDecodeError:
            logger.warning("[VLMCritic] JSON parse failed for verdict; defaulting REJECT")
            return CriticVerdict(
                status="REJECT",
                score=0.0,
                reason=f"Parse error: {raw[:120]}",
                attempt=attempt,
            )

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _encode_image(self, image: np.ndarray) -> str:
        """Encode a BGR cv2 frame to base64 JPEG for the OpenAI vision API."""
        _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.b64encode(buf.tobytes()).decode("utf-8")

    def _call_api(self, system: str, user: str, b64_image: str) -> str:
        """Make a GPT-4o vision API call and return the raw text response."""
        response = self._client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=512,
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                # "low" detail = cheap & fast, sufficient for scene understanding
                                "url": f"data:image/jpeg;base64,{b64_image}",
                                "detail": "low",
                            },
                        },
                        {"type": "text", "text": user},
                    ],
                },
            ],
        )
        return response.choices[0].message.content.strip()


# ── CLI test ──────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
    )

    parser = argparse.ArgumentParser(description="Test VLMCritic standalone")
    parser.add_argument("--test_image", default=None,
                        help="Path to a test image (optional in mock mode)")
    parser.add_argument("--live", action="store_true",
                        help="Use real GPT-4o API (requires OPENAI_API_KEY)")
    parser.add_argument("--task", default="pick and place red cube to side area")
    parser.add_argument("--attempts", type=int, default=2,
                        help="Number of attempts to simulate (default: 2)")
    args = parser.parse_args()

    critic = VLMCritic(mock=not args.live)

    if args.test_image and Path(args.test_image).exists():
        frame = cv2.imread(args.test_image)
    else:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        logger.warning("No test image — using blank frame")

    for attempt in range(1, args.attempts + 1):
        print(f"\n{'='*60}")
        print(f"  Attempt {attempt}")
        print(f"{'='*60}")

        plan    = critic.propose(frame, args.task, attempt=attempt)
        print(plan.pretty())

        verdict = critic.verify(frame, plan, attempt=attempt)
        print(verdict.pretty())

        if verdict.accepted:
            print("\n  -> Plan ACCEPTED. Robot would execute now.")
            break
        else:
            print("\n  -> Plan REJECTED. Reflecting and retrying...")

    print("\nDone.")


if __name__ == "__main__":
    _cli()
