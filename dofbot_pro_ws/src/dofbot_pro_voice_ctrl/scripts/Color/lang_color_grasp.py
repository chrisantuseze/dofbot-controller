#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lang_color_grasp.py
===================
Standalone pick-and-place executor for DOFBOT Pro with parameterized drop targets
and language-level subtask orchestration.

Supported Drop Targets:
  - 'left_bin' / 'left':    Joint 1 = 150 deg
  - 'right_bin' / 'right':  Joint 1 = 30 deg
  - 'center_bin' / 'center': Joint 1 = 90 deg
  - 'default' / 'storage_bin': Left bin (150 deg)

Topics:
  - Subscribes: /xyz (Position), /target_placement (String), /subtask_cmd (String)
  - Publishes: /TargetAngle (ArmJoint), /grasp_done (Bool), /subtask_done (String)
"""

import os
import sys
import time
import math
import json
import threading
import yaml
from typing import Dict, List, Optional, Tuple

import rospy
import numpy as np
from std_msgs.msg import Float32, Bool, Int8, String
from sensor_msgs.msg import JointState
import transforms3d as tfs
import tf.transformations as tf
import rospkg

from dofbot_pro_info.msg import ArmJoint, Position
from dofbot_pro_info.srv import kinemarics, kinemaricsRequest, kinemaricsResponse

# Drop Target Configurations: [j1_base, j2, j3, j4, j5, j6_gripper]
DROP_PRESETS: Dict[str, List[float]] = {
    "left_bin":    [170.0, 40.0, 50.0, 30.0, 90.0, 135.0],
    "left":        [170.0, 40.0, 50.0, 30.0, 90.0, 135.0],
    "right_bin":   [30.0,  55.0, 34.0, 16.0, 90.0, 135.0],
    "right":       [30.0,  55.0, 34.0, 16.0, 90.0, 135.0],
    "center_bin":  [90.0,  55.0, 34.0, 16.0, 90.0, 135.0],
    "center":      [90.0,  55.0, 34.0, 16.0, 90.0, 135.0],
    "storage_bin": [170.0, 40.0, 50.0, 30.0, 90.0, 135.0],
    "default":     [170.0, 40.0, 50.0, 30.0, 90.0, 135.0],
}

COLOR_IDS = {
    "red": 7,
    "green": 8,
    "blue": 9,
    "yellow": 10
}


class LangColorGraspNode:
    def __init__(self):
        rospy.init_node("lang_color_grasp", anonymous=False)

        # Load calibration offsets
        self.offset_config = self._load_offsets()
        self.x_offset = self.offset_config.get("x_offset", 0.0)
        self.y_offset = self.offset_config.get("y_offset", 0.0)
        self.z_offset = self.offset_config.get("z_offset", 0.0)
        rospy.loginfo(f"[lang_color_grasp] Offsets: x={self.x_offset}, y={self.y_offset}, z={self.z_offset}")

        # Publishers & Subscribers
        self.pub_target_angle = rospy.Publisher("TargetAngle", ArmJoint, queue_size=1)
        self.pub_grasp_done = rospy.Publisher("grasp_done", Bool, queue_size=1)
        self.pub_subtask_done = rospy.Publisher("subtask_done", String, queue_size=1)
        self.pub_voice = rospy.Publisher("voice_result", Int8, queue_size=1)

        self.sub_xyz = rospy.Subscriber("xyz", Position, self.on_xyz, queue_size=1)
        self.sub_placement = rospy.Subscriber("target_placement", String, self.on_target_placement, queue_size=1)
        self.sub_cmd = rospy.Subscriber("subtask_cmd", String, self.on_subtask_cmd, queue_size=1)
        # Servo read-back from arm_driver; used to re-send moves the serial bus dropped (seen: joint 3 ignored a home).
        self.cur_joints = None
        self.sub_js = rospy.Subscriber("joint_states", JointState, self._on_joint_states, queue_size=1)

        # Kinematics service client
        self.kin_client = rospy.ServiceProxy("get_kinemarics", kinemarics)

        # Joint configurations
        self.init_joints = [90.0, 120.0, 0.0, 0.0, 90.0, 30.0]
        self.current_drop_target = "left_bin"
        self.gripper_joint = 90
        self.gripper_close_angle = rospy.get_param("~gripper_close_angle", 145)

        self.CurEndPos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.camera_info_K = [477.57421875, 0.0, 319.3820495605469, 0.0, 477.55718994140625, 238.64108276367188, 0.0, 0.0, 1.0]
        self.EndToCamMat = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 7.96326711e-04, 9.99999683e-01, -9.90000000e-02],
            [0.0, -9.99999683e-01, 7.96326711e-04, 4.90000000e-02],
            [0.0, 0.0, 0.0, 1.0]
        ])

        self.grasp_lock = threading.Lock()
        self.is_busy = False
        self.current_subtask_info = {}
        self.current_action = "pick_place"      # pick_place | pick | place_on | place_at
        # Height added on top of the detected surface when placing a held block on another block.
        # Start high (safe drop) and tune down live:  rosparam set /lang_color_grasp/stack_dz 0.035
        self.default_stack_dz = 0.05
        # Base-block poses located BEFORE the pick (color -> (world pose, time)), so place_on never has to
        # detect the base while the arm is holding another block. Filled by the "locate" action.
        self.cached_base = {}
        self.locating = False
        self.cache_max_age = 300.0
        self.pub_status = rospy.Publisher("detect_status", String, queue_size=5)

        self.get_current_end_pos()
        rospy.sleep(0.5)
        self.pub_arm(self.init_joints)
        rospy.loginfo("[lang_color_grasp] Node initialized and arm homed.")

    def _load_offsets(self) -> dict:
        try:
            param_path = os.path.join(rospkg.RosPack().get_path("dofbot_pro_info"), "param", "offset_value.yaml")
        except Exception:
            param_path = "/home/jetson/echris/dofbot-controller/dofbot_pro_ws/src/dofbot_pro_info/param/offset_value.yaml"

        if os.path.exists(param_path):
            with open(param_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_current_end_pos(self):
        try:
            self.kin_client.wait_for_service(timeout=5.0)
            req = kinemaricsRequest()
            req.cur_joint1 = self.init_joints[0]
            req.cur_joint2 = self.init_joints[1]
            req.cur_joint3 = self.init_joints[2]
            req.cur_joint4 = self.init_joints[3]
            req.cur_joint5 = self.init_joints[4]
            req.kin_name = "fk"
            resp = self.kin_client.call(req)
            if isinstance(resp, kinemaricsResponse):
                self.CurEndPos = [resp.x, resp.y, resp.z, resp.Roll, resp.Pitch, resp.Yaw]
                rospy.loginfo(f"[lang_color_grasp] Current End Pose: {self.CurEndPos}")
        except Exception as e:
            rospy.logwarn(f"[lang_color_grasp] FK call failed: {e}")

    def on_target_placement(self, msg: String):
        target = msg.data.lower().strip()
        if target in DROP_PRESETS:
            self.current_drop_target = target
            rospy.loginfo(f"[lang_color_grasp] Target drop preset set to: '{target}'")
        else:
            rospy.logwarn(f"[lang_color_grasp] Unknown drop target '{target}', defaulting to left_bin")
            self.current_drop_target = "left_bin"

    def on_subtask_cmd(self, msg: String):
        try:
            cmd = json.loads(msg.data)
            color = cmd.get("color", "").lower().strip()
            target = cmd.get("target", "left_bin").lower().strip()
            self.current_drop_target = target if target in DROP_PRESETS else "left_bin"
            self.current_subtask_info = cmd
            self.current_action = cmd.get("action", "pick_place")
            self.locating = self.current_action == "locate"

            # Acknowledge at once (the client retries until it sees this). The arm is homed only when a new
            # task starts (action "reset", sent by the pipeline), never between the subtasks of one task.
            self.pub_status.publish(String(data=json.dumps({"status": "searching", "color": color, "ack": True})))
            if self.current_action == "reset":
                if self.is_busy:
                    rospy.logwarn("[lang_color_grasp] Arm busy; reset ignored.")
                else:
                    self._go_home(keep_gripper=False)
                self.pub_subtask_done.publish(String(data=json.dumps(
                    {"status": "success", "reset": True, "timestamp": time.time()})))
                return

            cached = self.cached_base.get(color)
            if self.current_action in ("place_on", "place_at") and cached and time.time() - cached[1] < self.cache_max_age:
                rospy.loginfo(f"[lang_color_grasp] {self.current_action} using base '{color}' pose cached before the pick: {cached[0]}")
                threading.Thread(target=self._execute_grasp_pipeline, args=(list(cached[0]),)).start()
                return

            color_id = COLOR_IDS.get(color)
            if color_id:
                rospy.loginfo(f"[lang_color_grasp] Triggering subtask: Color={color} (ID {color_id}) -> Target={self.current_drop_target}")
                self.pub_voice.publish(Int8(data=color_id))
            else:
                rospy.logerr(f"[lang_color_grasp] Invalid color in command: {color}")
        except Exception as e:
            rospy.logerr(f"[lang_color_grasp] Failed to parse subtask_cmd: {e}")

    def _go_home(self, keep_gripper: bool = False):
        """Move to the observation pose (detection and IK both assume it). keep_gripper: don't drop a held block."""
        pose = list(self.init_joints)
        if keep_gripper:
            pose[5] = self.gripper_close_angle
        rospy.loginfo(f"[lang_color_grasp] Homing arm to {pose}")
        self._safe_home(pose)

    def on_xyz(self, msg: Position):
        if self.is_busy:
            rospy.logwarn_throttle(2.0, "[lang_color_grasp] Arm is currently busy. Ignoring xyz message.")
            return

        if msg.z == 0.0:
            return

        camera_loc = self.pixel_to_camera_depth((msg.x, msg.y), msg.z)
        pose_end_mat = np.matmul(self.EndToCamMat, self.xyz_euler_to_mat(camera_loc, (0, 0, 0)))
        end_point_mat = self.get_end_point_mat()
        world_pose = np.matmul(end_point_mat, pose_end_mat)
        pose_t, _ = self.mat_to_xyz_euler(world_pose)

        pose_t[0] += self.x_offset
        pose_t[1] += self.y_offset
        pose_t[2] += self.z_offset

        if self.locating:
            # locate: remember where this block is, do not move the arm
            self.locating = False
            color = self.current_subtask_info.get("color", "")
            self.cached_base[color] = (list(pose_t), time.time())
            rospy.loginfo(f"[lang_color_grasp] Located '{color}' at world pose {pose_t}; cached.")
            self.pub_subtask_done.publish(String(data=json.dumps(
                {"status": "success", "located": color, "pose": [float(v) for v in pose_t], "timestamp": time.time()})))
            return

        threading.Thread(target=self._execute_grasp_pipeline, args=(pose_t,)).start()

    def _execute_grasp_pipeline(self, pose_t):
        with self.grasp_lock:
            self.is_busy = True
            try:
                rospy.loginfo(f"[lang_color_grasp] Executing grasp to world pose: {pose_t}")
                resp = self._ik(pose_t[0], pose_t[1], pose_t[2])
                joints = [
                    resp.joint1,
                    resp.joint2,
                    resp.joint3,
                    min(90.0, resp.joint4),
                    90.0,
                    30.0
                ]
                rospy.loginfo(f"[lang_color_grasp] Computed IK joints: {joints}")

                action = self.current_action
                if action in ("place_on", "place_at"):
                    if action == "place_at":
                        # Rearrangement: set the held block down on the table beside the reference block.  The
                        # reference block's grasp pose is at table grasp height, so aim there plus a small
                        # release height.  "left" = world -x (image left).  Live tuning:
                        #   rosparam set /lang_color_grasp/place_gap 0.07   (centre to centre, metres)
                        #   rosparam set /lang_color_grasp/place_dz 0.01
                        side = -1.0 if self.current_subtask_info.get("target") == "left_of" else 1.0
                        dz = rospy.get_param("~place_dz", 0.01)
                        dx, dy, dyaw = side * rospy.get_param("~place_gap", 0.07), 0.0, 0.0
                    else:
                        # Hover-then-lower over the detected base block, holding the picked block.
                        dz = rospy.get_param("~stack_dz", self.default_stack_dz)
                        # Live nudges (metres / degrees), e.g.:
                        #   rosparam set /lang_color_grasp/stack_dx 0.01
                        #   rosparam set /lang_color_grasp/stack_dyaw 15     (wrist joint 5 = 90 + dyaw)
                        dx = rospy.get_param("~stack_dx", 0.0)
                        dy = rospy.get_param("~stack_dy", 0.0)
                        dyaw = rospy.get_param("~stack_dyaw", 0.0)
                    target = [pose_t[0] + dx, pose_t[1] + dy, pose_t[2]]
                    lower = rospy.get_param("~ik_lower_on_saturation", False)
                    # release pose (the one that stacked successfully), reached from above:
                    # 1. move across with the shoulder raised  2. lower to the release pose  3. release (below)
                    joints, dz = self._hover_joints(target, dz, self.gripper_close_angle, dyaw, lower)
                    high = self._lifted(joints)
                    # Optional: finish the joint-1 turn from a fixed side (~j1_approach_deg) and trim it (~j1_trim_deg).
                    over = rospy.get_param("~j1_approach_deg", 0.0)   # measured j1 was within 1 deg: off by default
                    trim = rospy.get_param("~j1_trim_deg", 0.0)
                    high[0] += trim
                    joints[0] += trim
                    if over > 0:
                        pre = list(high)
                        pre[0] = high[0] - over
                        self.pub_target_arm(pre, angle=self.gripper_close_angle, runtime=2500)
                    rospy.loginfo(f"[lang_color_grasp] {action} move above target: {high}")
                    self.pub_target_arm(high, angle=self.gripper_close_angle, runtime=1500 if over > 0 else 2500)
                    time.sleep(1.0)
                    rospy.loginfo(f"[lang_color_grasp] {action} lower (dz={dz}, dx={dx}, dy={dy}, dyaw={dyaw}): {joints}")
                    self.pub_target_arm(joints, angle=self.gripper_close_angle, runtime=2000)
                    time.sleep(0.5)
                    rospy.loginfo(f"[lang_color_grasp] {action} release: joint1 target {joints[0]:.1f}, actual "
                                  f"{self.cur_joints[0] if self.cur_joints else float('nan'):.1f}")
                    self._place_high = high
                    self._release_and_retreat()
                    self.cached_base.pop(self.current_subtask_info.get("color", ""), None)
                else:
                    # Move to target object: above it first, then straight down, so the gripper never sweeps in
                    # from the side/top onto the block's end.
                    self.pub_target_arm(self._lifted(joints), runtime=2500)
                    self.pub_target_arm(joints, runtime=1500)
                    time.sleep(1.0)
                    if action == "pick":
                        self._grasp_and_hold(joints)   # keep the block, lift slightly, stay put
                    else:
                        self._move_and_deposit()    # grasp, lift, drop in the bin, return

                # Report completion
                self.pub_grasp_done.publish(Bool(data=True))
                result_payload = {
                    "status": "success",
                    "drop_target": self.current_drop_target,
                    "pose": [float(v) for v in pose_t],   # world pose of the detected / cached block
                    "info": self.current_subtask_info,
                    "timestamp": time.time()
                }
                self.pub_subtask_done.publish(String(data=json.dumps(result_payload)))
                rospy.loginfo("[lang_color_grasp] Subtask execution completed successfully.")
            except Exception as e:
                rospy.logerr(f"[lang_color_grasp] Grasp execution error: {e}")
                fail_payload = {"status": "error", "error": str(e), "timestamp": time.time()}
                self.pub_subtask_done.publish(String(data=json.dumps(fail_payload)))
            finally:
                self.is_busy = False

    def _hold_pose(self, gripper: float, j1=None, j2=None):
        """Full 6-joint pose = the MEASURED arm pose with an optional joint-1 / joint-2 target and an explicit
        gripper angle.  Sending a full pose is what routes a move through _send_joints (read-back + re-send);
        the untouched joints are commanded to where they already are, so only the named joint is really tested.
        None when /joint_states has not arrived yet -- the caller then falls back to a single-servo write."""
        cur = self.cur_joints
        if cur is None:
            return None
        pose = [float(v) for v in cur[:5]] + [float(gripper)]
        if j1 is not None:
            pose[0] = float(j1)
        if j2 is not None:
            pose[1] = float(j2)
        return pose

    def _carry_move(self, what: str, gripper: float, run_time=2000, j1=None, j2=None, fallback=None):
        """One step of the deposit taken while the block is held, sent as a full pose so the move is verified.
        Raises if the joint never got there: the single-servo writes used before were never read back, and a
        lift that joint 2 ignored was followed by the base turn, which dragged the block across the table
        (measured: joint 2 needed a re-send on 3 of 8 bin descents in the 2026-09-23 task1c session)."""
        pose = self._hold_pose(gripper, j1=j1, j2=j2)
        if pose is None:
            sid, angle = fallback
            self.pub_arm([], id=sid, angle=angle, run_time=run_time)
            time.sleep(run_time / 1000.0 + 0.5)
            return
        if not self.pub_arm(pose, run_time=run_time):
            raise RuntimeError(f"{what}: joint did not reach target while holding the block "
                               f"(see the 'joints off target' warning above)")
        time.sleep(0.3)

    def _move_and_deposit(self):
        drop_joints = list(DROP_PRESETS.get(self.current_drop_target, DROP_PRESETS["left_bin"]))
        # Live tuning, no restart needed, e.g.:
        #   rosparam set /lang_color_grasp/drop_left_bin "[150, 60, 30, 16, 90, 135]"
        override = rospy.get_param(f"~drop_{self.current_drop_target}", None)
        if override is not None and len(override) == 6:
            drop_joints = [float(v) for v in override]
            rospy.loginfo(f"[lang_color_grasp] Using drop override for '{self.current_drop_target}': {drop_joints}")
        base_drop_angle = drop_joints[0]
        hold = self.gripper_close_angle

        # 1. Wrist upright.  id 5 is Arm5_Joint, NOT the gripper (that is id 6) -- the gripper was already
        #    opened to 30 by the approach pose, so this only squares the wrist.
        self.pub_arm([], id=5, angle=self.gripper_joint, run_time=2000)
        time.sleep(2.2)

        # 2. Close gripper on object.  Deliberately not verified: the jaws stall on the block well before
        #    reaching gripper_close_angle, so the read-back never matches the command.
        self.pub_arm([], id=6, angle=hold, run_time=2000)
        time.sleep(2.5)

        # 3. Lift the block clear of the table before anything rotates.
        self._carry_move("lift the held block", hold, j2=120.0, fallback=(2, 120.0))

        # 4. Turn base towards drop location.
        self._carry_move("turn towards the bin", hold, j1=base_drop_angle, fallback=(1, base_drop_angle))

        # 5. Lower into the bin, STILL HOLDING the block.  drop_joints[5] is a gripper angle and the driver's
        #    Arm_serial_servo_write6 applies all six values, so sending the preset unchanged opened the grip
        #    from gripper_close_angle to drop_joints[5] during the descent and could drop the block short of
        #    the bin.  The grip is kept until step 6 releases it deliberately.
        if not self.pub_arm(list(drop_joints[:5]) + [hold], run_time=2000):
            raise RuntimeError(f"arm did not reach the '{self.current_drop_target}' pose while holding the "
                               f"block; not releasing (see the 'joints off target' warning above)")
        time.sleep(0.3)

        # 6. Open gripper to release block
        self.pub_arm([], id=6, angle=90, run_time=2000)
        time.sleep(2.5)

        # 7. Raise shoulder clear of bin.  Not fatal -- the block is already released and _safe_home stages
        #    the lift itself.
        clear = self._hold_pose(90.0, j2=90.0)
        if clear is None:
            self.pub_arm([], id=2, angle=90, run_time=2000)
            time.sleep(2.2)
        elif not self.pub_arm(clear, run_time=2000):
            rospy.logwarn("[lang_color_grasp] shoulder did not clear the bin; homing will stage the lift")

        # 8. Return arm to init observation pose
        self._safe_home(self.init_joints)

    def _ik(self, x, y, z):
        """IK at the default gripper pitch. Close to the base that gives joint 3 < 0, which the servo can't do
        (it stops at 0 and the gripper lands off target), so steepen the pitch until joint 3 >= 0."""
        req = kinemaricsRequest()
        req.kin_name = "ik"
        req.tar_x, req.tar_y = x, y
        req.tar_z = z + (math.sqrt(x**2 + y**2) - 0.181) * 0.2
        roll = self.CurEndPos[3]
        for k in range(8):
            req.Roll = roll - 0.05 * k
            resp = self.kin_client.call(req)
            if resp.joint3 >= 0.0:
                if k:
                    rospy.loginfo(f"[lang_color_grasp] steeper gripper pitch {req.Roll:.2f} (joint3 was negative)")
                break
        return resp

    def _hover_joints(self, pose_t, dz, gripper, dyaw=0.0, lower=False):
        """IK for a hover `dz` above pose_t. With the fixed gripper orientation joint 3 saturates at 90 deg when
        the hover is high; the saturated pose still stacked correctly in testing, so lowering dz until joint 3
        is unsaturated is opt-in (lower=True / rosparam ~ik_lower_on_saturation)."""
        for _ in range(12):
            resp = self._ik(pose_t[0], pose_t[1], pose_t[2] + dz)
            if not lower or resp.joint3 < 85.0 or dz <= 0.0:
                break
            rospy.logwarn(f"[lang_color_grasp] hover dz={dz:.3f} unreachable (joint3={resp.joint3:.1f}); lowering")
            dz = max(0.0, dz - 0.005)
        joints = [resp.joint1, resp.joint2, resp.joint3, min(90.0, resp.joint4),
                  max(0.0, min(180.0, 90.0 + dyaw)), gripper]
        return joints, dz

    def _lifted(self, joints):
        """Raise the arm by rotating the shoulder (joint 2) up by ~lift_j2_deg (default 20), other joints unchanged.
        A Cartesian straight-up lift is not reachable at this distance (IK saturates and swings the wrist)."""
        j = list(joints)
        j[1] = min(180.0, j[1] + rospy.get_param("~lift_j2_deg", 20.0))
        return j

    def _grasp_and_hold(self, grasp_joints):
        """Grasp the block and lift it (shoulder up), staying over the pick spot. No homing: place_on uses the
        base pose cached by "locate", so nothing has to be detected between pick and place."""
        self.pub_arm([], id=5, angle=self.gripper_joint, run_time=2000)
        time.sleep(2.2)
        self.pub_arm([], id=6, angle=self.gripper_close_angle, run_time=2000)
        time.sleep(2.5)
        lifted = self._lifted(list(grasp_joints[:5]) + [self.gripper_close_angle])
        rospy.loginfo(f"[lang_color_grasp] Lifting held block: {lifted}")
        self.pub_arm(lifted, run_time=2000)
        time.sleep(2.5)

    def _release_and_retreat(self):
        """Open the gripper, rise straight back to carry height, then go to the observation pose (end of task)."""
        self.pub_arm([], id=6, angle=90, run_time=1500)
        time.sleep(2.0)
        high = getattr(self, "_place_high", None)
        if high is not None:
            self.pub_arm(list(high[:5]) + [90], run_time=1500)
            time.sleep(0.5)
        self._safe_home(self.init_joints)

    def _safe_home(self, pose):
        """Home in stages with the arm kept straight until the shoulder is up (checked with FK):
        1) joint 2 to 90 alone (the stretched-out lift joint 2 can do), 2) joint 2 to the home angle, arm still
        straight (low torque near vertical), 3) fold joints 3-5 / turn joint 1 into the home pose.
        Folding at joint 2 = 90 swept the gripper to ~4 cm high, 8 cm from the base axis -> hit the base."""
        cur = self.cur_joints
        if cur is not None and cur[1] < 85.0:
            self.pub_arm([cur[0], 90.0, cur[2], cur[3], cur[4], pose[5]], run_time=2000)
            cur = self.cur_joints or cur
        if cur is not None and cur[1] < pose[1] - 4.0:
            self.pub_arm([cur[0], pose[1], cur[2], cur[3], cur[4], pose[5]], run_time=1500)
        self.pub_arm(pose, run_time=2500)

    def get_end_point_mat(self):
        end_w, end_x, end_y, end_z = self.euler_to_quaternion(self.CurEndPos[3], self.CurEndPos[4], self.CurEndPos[5])
        return self.xyz_quat_to_mat([self.CurEndPos[0], self.CurEndPos[1], self.CurEndPos[2]], [end_w, end_x, end_y, end_z])

    def pixel_to_camera_depth(self, pixel_coords, depth):
        fx, fy = self.camera_info_K[0], self.camera_info_K[4]
        cx, cy = self.camera_info_K[2], self.camera_info_K[5]
        px, py = pixel_coords
        return np.array([(px - cx) * depth / fx, (py - cy) * depth / fy, depth])

    def xyz_euler_to_mat(self, xyz, euler):
        mat = tfs.euler.euler2mat(euler[0], euler[1], euler[2])
        return tfs.affines.compose(np.squeeze(np.asarray(xyz)), mat, [1, 1, 1])

    def euler_to_quaternion(self, roll, pitch, yaw):
        q = tf.quaternion_from_euler(roll, pitch, yaw)
        return np.array([q[3], q[0], q[1], q[2]])

    def xyz_quat_to_mat(self, xyz, quat):
        mat = tfs.quaternions.quat2mat(np.asarray(quat))
        return tfs.affines.compose(np.squeeze(np.asarray(xyz)), mat, [1, 1, 1])

    def mat_to_xyz_euler(self, mat):
        t, r, _, _ = tfs.affines.decompose(mat)
        return t, tfs.euler.mat2euler(r)

    def _on_joint_states(self, msg: JointState):
        # arm_driver publishes (deg - 90) in radians for joints 1-5 (the gripper uses a different mapping)
        self.cur_joints = [90.0 + math.degrees(v) for v in msg.position[:5]]

    def _send_joints(self, joints, run_time, tol=4.0, retries=2) -> bool:
        """Send a full 6-joint pose, wait for it, and re-send if a servo did not get there (dropped write).
        Returns False if it never got there, so a caller carrying a block can stop instead of continuing
        with the arm somewhere else entirely.  True when there is no read-back to judge by."""
        for attempt in range(retries + 1):
            arm_joint = ArmJoint()
            arm_joint.run_time = run_time
            arm_joint.joints = list(joints)
            self.pub_target_angle.publish(arm_joint)
            time.sleep(run_time / 1000.0 + 0.4)
            cur = self.cur_joints
            if cur is None:
                return True
            err = [abs(c - t) for c, t in zip(cur, joints[:5])]
            if max(err) <= tol:
                return True
            bad = {i + 1: (round(cur[i], 1), round(joints[i], 1)) for i, e in enumerate(err) if e > tol}
            rospy.logwarn(f"[lang_color_grasp] joints off target (joint: (actual, target)) {bad}; "
                          f"{'re-sending' if attempt < retries else 'giving up'}")
        return False

    def pub_target_arm(self, joints, id=6, angle=180, runtime=2000) -> bool:
        if len(joints) != 0:
            return self._send_joints(joints, runtime)
        arm_joint = ArmJoint()
        arm_joint.id = id
        arm_joint.angle = angle
        arm_joint.run_time = runtime
        arm_joint.joints = []
        self.pub_target_angle.publish(arm_joint)
        return True        # single-servo writes are not read back, so there is nothing to report

    def pub_arm(self, joints, id=1, angle=90, run_time=2000) -> bool:
        if len(joints) != 0:
            return self._send_joints(joints, run_time)
        arm_joint = ArmJoint()
        arm_joint.run_time = run_time
        arm_joint.id = id
        arm_joint.angle = angle
        self.pub_target_angle.publish(arm_joint)
        return True        # single-servo writes are not read back, so there is nothing to report


# ── Standalone Python Client for high-level scripting ──
class LanguageGraspClient:
    """Client class to trigger and monitor subtasks from Python code."""
    def __init__(self):
        if not rospy.core.is_initialized():
            rospy.init_node("lang_grasp_client", anonymous=True)
        self.pub_cmd = rospy.Publisher("subtask_cmd", String, queue_size=1)
        self._done_event = threading.Event()
        self._last_result = {}
        self.sub_done = rospy.Subscriber("subtask_done", String, self._on_done, queue_size=1)

    def _on_done(self, msg: String):
        try:
            self._last_result = json.loads(msg.data)
        except Exception:
            self._last_result = {"status": msg.data}
        self._done_event.set()

    def execute_subtask(self, color: str, target: str = "left_bin", timeout: float = 40.0,
                        action: str = "pick_place", base_color: str = None) -> bool:
        self._done_event.clear()
        self._last_result = {}
        # place_on / place_at: the detector must look for the BASE (reference) block; `held` is the block in the gripper
        payload = {"action": action, "color": base_color if action in ("place_on", "place_at") else color,
                   "held": color, "target": target}
        rospy.loginfo(f"[LanguageGraspClient] Dispatching: {payload}")
        self.pub_cmd.publish(String(data=json.dumps(payload)))

        finished = self._done_event.wait(timeout=timeout)
        if not finished:
            rospy.logwarn(f"[LanguageGraspClient] Timed out waiting for subtask completion after {timeout}s.")
            return False
        return self._last_result.get("status") == "success"


if __name__ == "__main__":
    try:
        node = LangColorGraspNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
