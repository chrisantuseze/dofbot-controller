#!/usr/bin/env python3
"""
verify2act/policy_executor.py
=============================
Python interface for Verify2Act systems to command the physical Dofbot Pro.

Phase 2 implementation: replaces the ACT neural-policy executor with the
VLM-Critic + HDF5-replay orchestrator (V2AOrchestrator).

The public API is unchanged — existing integration code continues to work:

    from verify2act.policy_executor import RealRobotPolicyExecutor

    executor = RealRobotPolicyExecutor(jetson_ip="192.168.0.8")
    executor.execute("pick and place red cube to side area")
    executor.close()

Internally, each execute() call runs one full Verify2Act loop:
  Propose → Verify → (Reflect →) Act (replay pre-recorded HDF5 episode)
"""

import sys
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from verify2act.v2a_orchestrator import V2AOrchestrator


class RealRobotPolicyExecutor:
    """
    High-level executor for the Verify2Act Phase-2 pipeline.

    Args:
        jetson_ip:    IP of the Jetson running rosbridge (default 192.168.0.8).
        bridge_port:  rosbridge WebSocket port (default 9090).
        speed:        HDF5 replay speed scaling — 0.4 = 40% of recorded speed.
        gripper_max:  Soft gripper close ceiling in servo degrees (default 118).
        max_attempts: Number of Propose→Verify cycles before giving up (default 2).
        mock_vlm:     True = scripted GPT-4o mock (default). False = live API call.
        dry_run:      True = offline test, no robot commands sent.
    """

    def __init__(
        self,
        jetson_ip: str = "192.168.0.8",
        bridge_port: int = 9090,
        speed: float = 0.4,
        gripper_max: float = 118.0,
        gripper_margin: float = 2.0,
        max_attempts: int = 2,
        mock_vlm: bool = True,
        dry_run: bool = False,
        # Legacy ACT args (ignored in Phase 2 — kept for API compatibility)
        checkpoint_dir: str = "",
        device: str = "cuda",
    ):
        self._orch = V2AOrchestrator(
            jetson_ip     = jetson_ip,
            bridge_port   = bridge_port,
            speed         = speed,
            gripper_max   = gripper_max,
            gripper_margin= gripper_margin,
            max_attempts  = max_attempts,
            mock_vlm      = mock_vlm,
            dry_run       = dry_run,
        )

    def execute(self, instruction: str, duration_s: float = 22.0) -> bool:
        """
        Execute a language instruction via the Verify2Act loop.

        Args:
            instruction: Natural-language task, e.g. "pick and place red cube".
            duration_s:  (Unused in Phase 2 — kept for API compatibility.)
        Returns:
            True if the task was executed successfully, False otherwise.
        """
        self._orch.task = instruction
        try:
            return self._orch.run()
        except Exception as e:
            print(f"[Executor Error]: {e}")
            return False

    def close(self):
        """Disconnect from the robot and clean up resources."""
        self._orch.close()
