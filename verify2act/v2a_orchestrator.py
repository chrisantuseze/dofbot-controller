#!/usr/bin/env python3
"""
verify2act/v2a_orchestrator.py
================================
Verify2Act main orchestration loop for the real Dofbot Pro robot.

Implements the core Propose → Verify → (Reflect →) Act cycle:

  For each attempt (up to max_attempts):
    1. Capture a live camera snapshot from the robot via roslibpy
    2. Call VLMCritic.propose()  → high-level plan
    3. Call VLMCritic.verify()   → ACCEPT or REJECT verdict
    4. If REJECT: log the card, pause (for video), continue to next attempt
    5. If ACCEPT: replay the matching pre-recorded HDF5 episode on the robot

Episode mapping (edit to add more tasks/configurations):
    attempt 1 → episode_000000.hdf5  (failure / approach blocked)
    attempt 2 → episode_000001.hdf5  (success / obstacle clearance)

Usage:
    # Dry-run (no robot, mock VLM):
    python3 verify2act/v2a_orchestrator.py --dry_run

    # Full demo with real robot:
    python3 verify2act/v2a_orchestrator.py \\
        --jetson_ip 192.168.0.8 \\
        --task "pick and place red cube to side area" \\
        --speed 0.4

    # Switch to live GPT-4o (requires OPENAI_API_KEY):
    python3 verify2act/v2a_orchestrator.py --live_vlm --jetson_ip 192.168.0.8
"""

import argparse
import base64
import json
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Optional, List

import cv2
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from verify2act.vlm_critic import VLMCritic, VLMPlan, CriticVerdict

logger = logging.getLogger(__name__)

# ── Episode map ───────────────────────────────────────────────────────────────
# Maps attempt number → HDF5 file path (relative to project root).
# Attempt 1 replays the *failure* demo; attempt 2 replays the *success* demo.
DEFAULT_EPISODE_MAP = {
    1: "verify2act/dataset/episode_000000.hdf5",
    2: "verify2act/dataset/episode_000001.hdf5",
}

# ── Timing ────────────────────────────────────────────────────────────────────
CARD_DISPLAY_PAUSE_S = 3.0   # seconds to hold after showing verdict (for video)
PRE_EXEC_PAUSE_S     = 1.5   # pause before robot starts moving (for video)

BANNER = "=" * 66


def _banner(text: str) -> None:
    print(f"\n{BANNER}\n  {text}\n{BANNER}")


# ── Camera snapshot helper ────────────────────────────────────────────────────

class _CameraCapture:
    """
    Subscribes to the camera topic via roslibpy and buffers the latest frame.
    Exposes .get_frame() which returns a BGR numpy array or None.
    """

    def __init__(self, ros_client, topic: str = "/camera/color/image_raw"):
        self._frame = None
        self._lock  = threading.Lock()
        self._sub   = None
        self._ros   = ros_client
        self._topic = topic

    def start(self):
        try:
            import roslibpy
            self._sub = roslibpy.Topic(
                self._ros, self._topic, "sensor_msgs/Image", throttle_rate=500
            )
            self._sub.subscribe(self._on_image)
            logger.info("[Camera] Subscribed to %s", self._topic)
        except Exception as e:
            logger.warning("[Camera] Could not subscribe: %s", e)

    def stop(self):
        if self._sub:
            try:
                self._sub.unsubscribe()
            except Exception:
                pass

    def get_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def wait_for_frame(self, timeout: float = 10.0) -> Optional[np.ndarray]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            f = self.get_frame()
            if f is not None:
                return f
            time.sleep(0.1)
        return None

    def _on_image(self, msg: dict):
        try:
            h = msg["height"]; w = msg["width"]
            encoding = msg["encoding"]
            data = msg["data"]
            raw = base64.b64decode(data) if isinstance(data, str) else bytes(data)
            img = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3).copy()
            if encoding == "rgb8":
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img = cv2.flip(img, 0)   # match data_collector convention
            with self._lock:
                self._frame = img
        except Exception:
            pass


# ── Orchestrator ──────────────────────────────────────────────────────────────

class V2AOrchestrator:
    """
    Verify2Act orchestration loop.

    Args:
        task:          Natural-language task description.
        jetson_ip:     IP of the Jetson running rosbridge (ignored in dry_run).
        bridge_port:   rosbridge WebSocket port (default 9090).
        episode_map:   Dict mapping attempt → HDF5 path.
        speed:         Replay speed scaling (< 1 = slower/safer).
        gripper_max:   Soft gripper close limit (degrees).
        max_attempts:  Maximum number of PROPOSE→VERIFY cycles.
        mock_vlm:      If True, use scripted VLM responses (default True).
        dry_run:       If True, skip all robot/ROS calls (offline testing).
    """

    def __init__(
        self,
        task: str = "pick and place red cube to side area",
        jetson_ip: str = "192.168.0.8",
        bridge_port: int = 9090,
        episode_map: Optional[dict] = None,
        speed: float = 0.4,
        gripper_max: float = 118.0,
        gripper_margin: float = 2.0,
        max_attempts: int = 2,
        mock_vlm: bool = True,
        dry_run: bool = False,
    ):
        self.task           = task
        self.jetson_ip      = jetson_ip
        self.bridge_port    = bridge_port
        self.episode_map    = episode_map or DEFAULT_EPISODE_MAP
        self.speed          = speed
        self.gripper_max    = gripper_max
        self.gripper_margin = gripper_margin
        self.max_attempts   = max_attempts
        self.dry_run        = dry_run

        # Build episode map with resolved absolute paths
        self._episode_paths = {
            k: (_ROOT / v).resolve()
            for k, v in self.episode_map.items()
        }

        self.critic  = VLMCritic(mock=mock_vlm)
        self._ros    = None
        self._robot  = None
        self._camera = None

        if not dry_run:
            self._connect()

    # ── Connection ────────────────────────────────────────────────────────────

    def _connect(self):
        try:
            import roslibpy
        except ImportError:
            raise ImportError("roslibpy not installed. Run: pip install roslibpy")

        logger.info("[Orchestrator] Connecting to rosbridge %s:%d …",
                    self.jetson_ip, self.bridge_port)
        self._ros = roslibpy.Ros(host=self.jetson_ip, port=self.bridge_port)
        self._ros.run()

        deadline = time.time() + 15.0
        while not self._ros.is_connected and time.time() < deadline:
            time.sleep(0.2)
        if not self._ros.is_connected:
            raise ConnectionError(
                f"Failed to connect to rosbridge at {self.jetson_ip}:{self.bridge_port}"
            )
        logger.info("[Orchestrator] Connected.")

        # Import the existing RobotInterface from replay_on_robot
        from verify2act.replay_on_robot import RobotInterface
        self._robot = RobotInterface(jetson_ip=self.jetson_ip, port=self.bridge_port)
        self._robot._client = self._ros   # reuse existing connection
        # Re-register publishers/subscribers on the shared client
        self._robot.connect.__func__   # just to check it exists
        _setup_robot_pubs(self._robot, self._ros)

        self._camera = _CameraCapture(self._ros)
        self._camera.start()
        time.sleep(1.0)   # let the subscription propagate

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> bool:
        """
        Execute the full Verify2Act loop.
        Returns True if the task succeeds, False otherwise.
        """
        _banner(f"Verify2Act — Task: {self.task}")
        print(f"  Max attempts : {self.max_attempts}")
        print(f"  VLM mode     : {'MOCK (scripted)' if self.critic.mock else 'LIVE (GPT-4o)'}")
        print(f"  Dry run      : {self.dry_run}\n")

        accepted_at: Optional[int] = None

        for attempt in range(1, self.max_attempts + 1):
            _banner(f"Attempt {attempt} / {self.max_attempts}")

            # ── 1. Capture scene ───────────────────────────────────────────
            frame = self._capture_frame()

            # ── 2. VLM Propose ─────────────────────────────────────────────
            print("\n[VLM] Proposing plan…")
            plan = self.critic.propose(frame, self.task, attempt=attempt)
            print(plan.pretty())

            # ── 3. VLM Verify ──────────────────────────────────────────────
            print("\n[Critic] Verifying plan…")
            verdict = self.critic.verify(frame, plan, attempt=attempt)
            print(verdict.pretty())

            # ── 4. Branch on verdict ───────────────────────────────────────
            if verdict.accepted:
                accepted_at = attempt
                print(f"\n[Orchestrator] Plan ACCEPTED at attempt {attempt}.")
                time.sleep(CARD_DISPLAY_PAUSE_S)
                success = self._execute_episode(attempt)
                if success:
                    _banner(f"SUCCESS — task completed at attempt {attempt}")
                else:
                    _banner("EXECUTION ERROR — episode replay failed")
                return success
            else:
                print(f"\n[Orchestrator] Plan REJECTED at attempt {attempt}. "
                      "Reflecting and retrying after pause…")
                time.sleep(CARD_DISPLAY_PAUSE_S)

        print(f"\n[Orchestrator] Exhausted {self.max_attempts} attempts without "
              "an ACCEPTED plan.")
        return False

    # ── Episode execution ─────────────────────────────────────────────────────

    def _execute_episode(self, attempt: int) -> bool:
        """Replay the pre-recorded HDF5 episode for this attempt."""
        episode_path = self._episode_paths.get(attempt)
        if episode_path is None:
            logger.error("[Orchestrator] No episode mapped for attempt %d", attempt)
            return False

        if not episode_path.exists():
            logger.error("[Orchestrator] HDF5 not found: %s", episode_path)
            return False

        print(f"\n[Orchestrator] Replaying episode: {episode_path.name}")
        print(f"  speed={self.speed}x  gripper_max={self.gripper_max}°")

        if self.dry_run:
            print("  [DRY RUN] Skipping robot execution.")
            time.sleep(2.0)
            return True

        try:
            import h5py
            from verify2act.replay_on_robot import replay_episode

            time.sleep(PRE_EXEC_PAUSE_S)

            # Put robot into running state
            self._robot.send_cmd("start")
            time.sleep(0.5)

            replay_episode(
                hdf5_path         = episode_path,
                robot             = self._robot,
                speed             = self.speed,
                wait_for_ready    = True,
                gripper_max_deg   = self.gripper_max,
                gripper_margin_deg= self.gripper_margin,
                base_move_time_ms = 200,
            )
            return True

        except Exception as e:
            logger.error("[Orchestrator] Replay failed: %s", e, exc_info=True)
            return False

    # ── Camera ────────────────────────────────────────────────────────────────

    def _capture_frame(self) -> np.ndarray:
        """Return the latest camera frame, or a blank placeholder."""
        if self.dry_run or self._camera is None:
            logger.info("[Camera] dry_run — returning blank frame")
            return np.zeros((480, 640, 3), dtype=np.uint8)

        frame = self._camera.wait_for_frame(timeout=8.0)
        if frame is None:
            logger.warning("[Camera] No frame received — using blank placeholder")
            return np.zeros((480, 640, 3), dtype=np.uint8)
        return frame

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def close(self):
        if self._camera:
            self._camera.stop()
        if self._ros and self._ros.is_connected:
            self._ros.terminate()
        logger.info("[Orchestrator] Shut down.")


# ── Helper: set up publishers on existing roslibpy Ros instance ───────────────

def _setup_robot_pubs(robot, ros):
    """
    Wire up RobotInterface publishers/subscribers on the given Ros client
    without triggering a second connect() (which would open a second WebSocket).
    """
    import roslibpy
    robot._action_pub = roslibpy.Topic(ros, "/policy/action", "dofbot_pro_info/ArmJoint")
    robot._cmd_pub    = roslibpy.Topic(ros, "/robot/cmd",     "std_msgs/String")
    robot._ready_sub  = roslibpy.Topic(ros, "/robot/ready",   "std_msgs/Bool")
    robot._ready_sub.subscribe(robot._on_ready)
    robot._action_pub.advertise()
    robot._cmd_pub.advertise()


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args():
    p = argparse.ArgumentParser(
        description="Verify2Act real-robot orchestration loop",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--task",
                   default="pick and place red cube to side area",
                   help="Natural-language task description")
    p.add_argument("--jetson_ip",   default="192.168.0.8")
    p.add_argument("--bridge_port", type=int, default=9090)
    p.add_argument("--speed",       type=float, default=0.4,
                   help="Replay speed scaling (0.4 = 40% of recorded speed)")
    p.add_argument("--gripper_max", type=float, default=118.0,
                   help="Soft gripper close limit in degrees")
    p.add_argument("--max_attempts", type=int, default=2)
    p.add_argument("--dry_run", action="store_true",
                   help="Skip all robot/ROS calls — offline testing")
    p.add_argument("--live_vlm", action="store_true",
                   help="Use real GPT-4o API instead of scripted mock responses "
                        "(requires OPENAI_API_KEY)")
    return p.parse_args()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
    )
    args = _parse_args()

    orch = V2AOrchestrator(
        task          = args.task,
        jetson_ip     = args.jetson_ip,
        bridge_port   = args.bridge_port,
        speed         = args.speed,
        gripper_max   = args.gripper_max,
        max_attempts  = args.max_attempts,
        mock_vlm      = not args.live_vlm,
        dry_run       = args.dry_run,
    )

    try:
        success = orch.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[Orchestrator] Interrupted by user.")
    finally:
        orch.close()


if __name__ == "__main__":
    main()
