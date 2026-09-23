#!/usr/bin/env python3
"""
grasp_calibration.py  (v4)
===========================
Fully automatic grasp calibration using depth camera — no ruler needed.

Key insight from the data:
  - Run 2 showed IK error = 0.5 cm (IK solver is accurate)
  - depth=0 from grasp position = cube IS within 30 cm of camera = arm IS close
  - So position calibration is approximately correct
  - The likely remaining issue: gripper approach z-height
  - This script computes the correction automatically using peripheral depth
    around the detected blob even when the centre depth saturates to 0

Algorithm
─────────
1. HOME: detect cube → compute IK target T (what color_grasp sends to arm)
2. Trigger grasp, wait for arm to settle (3.5 s)
3. Snapshot joints → FK → actual gripper position G
4. Grab fresh frame from grasp position → try to re-detect cube
     • If blob centre depth = 0 (arm very close), sample the RING around blob
     • Estimate cube world position P₁ from best available depth
5. Δoffset = P₁ − T  → apply to offset_value.yaml
"""

import sys, os, math, time, threading, yaml
import numpy as np
import rospy
import cv2

sys.path.append('/home/jetson/echris/dofbot-controller/dofbot_pro_ws/devel/lib/python3/dist-packages')

from std_msgs.msg    import Int8
from sensor_msgs.msg import JointState, Image
from dofbot_pro_info.srv import dofbot_pro_kinemarics, dofbot_pro_kinemaricsRequest
from dofbot_pro_info.msg import Position
from cv_bridge       import CvBridge
import transforms3d as tfs
import tf.transformations as tf_t

# ── Config ────────────────────────────────────────────────────────────────────
OFFSET_FILE  = "/home/jetson/echris/dofbot-controller/dofbot_pro_ws/src/dofbot_pro_info/param/offset_value.yaml"
HSV_FILE     = "/home/jetson/echris/dofbot-controller/dofbot_pro_ws/src/dofbot_pro_voice_ctrl/scripts/Color/red_colorHSV.text"
DEBUG_OUT    = "/home/jetson/echris/dofbot-controller/debug_output"
INIT_JOINTS  = [90.0, 120.0, 0.0, 0.0, 90.0]
FX, FY, CX, CY = 477.574, 477.557, 319.382, 238.641
END_TO_CAM = np.array([
    [1.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00],
    [0.00000000e+00, 7.96326711e-04, 9.99999683e-01,-9.90000000e-02],
    [0.00000000e+00,-9.99999683e-01, 7.96326711e-04, 4.90000000e-02],
    [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 1.00000000e+00]
])
INITIAL_WAIT_SECS = 2.0   # wait at minimum before polling (IK computation time)
STABILITY_DEG   = 0.6    # consider stable when all joints change < this many degrees
STABILITY_RUNS  = 4      # consecutive stable readings required
STABILITY_POLL  = 0.4    # seconds between stability polls
MAX_WAIT_SECS   = 12.0   # give up waiting after this long

# ── Geometry ──────────────────────────────────────────────────────────────────

def read_hsv(path):
    vals = [int(v) for v in open(path).readline().split(',')]
    return (tuple(vals[:3]), tuple(vals[3:6]))

def compose_mat(xyz, euler=(0,0,0)):
    return tfs.affines.compose(np.asarray(xyz,float), tfs.euler.euler2mat(*euler), [1,1,1])

def compose_mat_quat(xyz, q):
    return tfs.affines.compose(np.asarray(xyz,float), tfs.quaternions.quat2mat(np.asarray(q)), [1,1,1])

def decompose_xyz(mat):
    t,_,_,_ = tfs.affines.decompose(mat); return t

def pixel_to_cam(px, py, depth):
    return np.array([(px-CX)*depth/FX, (py-CY)*depth/FY, depth])

def cam_to_world(cam_xyz, fk_pos, fk_rpy):
    q = tf_t.quaternion_from_euler(*fk_rpy)
    q_w = np.array([q[3], q[0], q[1], q[2]])
    end_mat  = compose_mat_quat(fk_pos, q_w)
    pose_end = np.matmul(END_TO_CAM, compose_mat(cam_xyz))
    return decompose_xyz(np.matmul(end_mat, pose_end))

def rad_to_servo(rads):
    return [math.degrees(r) + 90.0 for r in rads]

def fk(kin, joints5):
    r = dofbot_pro_kinemaricsRequest()
    r.cur_joint1, r.cur_joint2, r.cur_joint3, r.cur_joint4, r.cur_joint5 = joints5
    r.kin_name = 'fk'
    res = kin.call(r)
    return np.array([res.x, res.y, res.z]), np.array([res.Roll, res.Pitch, res.Yaw])

def robust_depth(depth_img, cx, cy, blob_r, min_valid_depth_mm=100):
    """Return median depth in mm. If centre is 0, sample the ring around the blob."""
    h, w = depth_img.shape[:2]
    def patch_median(x0, x1, y0, y1):
        x0, x1 = max(0,x0), min(w,x1)
        y0, y1 = max(0,y0), min(h,y1)
        p = depth_img[y0:y1, x0:x1].astype(float)
        v = p[p >= min_valid_depth_mm]
        return float(np.median(v)) if len(v) else 0.0

    # Try centre patch (5×5)
    r = 5
    d = patch_median(int(cx)-r, int(cx)+r+1, int(cy)-r, int(cy)+r+1)
    if d > 0:
        return d, "centre"

    # Try ring (distance = blob_r * 0.6 from centre, full circle)
    ring_r = max(10, int(blob_r * 0.6))
    samples = []
    for angle in np.linspace(0, 2*math.pi, 24, endpoint=False):
        rx = int(cx + ring_r * math.cos(angle))
        ry = int(cy + ring_r * math.sin(angle))
        d = patch_median(rx-3, rx+4, ry-3, ry+4)
        if d > 0:
            samples.append(d)
    if samples:
        return float(np.median(samples)), "ring"

    # Try full blob bounding box
    r2 = int(blob_r)
    d = patch_median(int(cx)-r2, int(cx)+r2+1, int(cy)-r2, int(cy)+r2+1)
    return d, "bbox"

def detect_cube(rgb, depth, hsv_range, label="", min_r=8):
    hsv  = cv2.cvtColor(rgb, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(hsv_range[0]), np.array(hsv_range[1]))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  np.ones((5,5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, np.ones((3,3), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        print(f"  [{label}] No HSV contours found.")
        return None
    c = max(cnts, key=cv2.contourArea)
    (cx, cy), r = cv2.minEnclosingCircle(c)
    if r < min_r:
        print(f"  [{label}] Largest blob r={r:.0f}px < min {min_r}px (likely noise/arm reflection).")
        return None
    depth_mm, src = robust_depth(depth, cx, cy, r)
    depth_m = depth_mm / 1000.0
    print(f"  [{label}] blob px=({cx:.0f},{cy:.0f}) r={r:.0f}  depth={depth_m:.3f}m (from {src})")
    return cx, cy, r, depth_m

def grab_frame():
    bridge = CvBridge()
    rgb   = bridge.imgmsg_to_cv2(rospy.wait_for_message('/camera/color/image_raw', Image, timeout=8.0), 'bgr8')
    depth = bridge.imgmsg_to_cv2(rospy.wait_for_message('/camera/depth/image_raw', Image, timeout=8.0), 'passthrough')
    return rgb, depth

def save_annotated(path, rgb, cx, cy, r, label, extra_lines=()):
    img = rgb.copy()
    cv2.circle(img, (int(cx), int(cy)), int(r), (0,255,0), 2)
    cv2.circle(img, (int(cx), int(cy)), 5, (0,0,255), -1)
    cv2.putText(img, label, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,0), 2)
    for i, ln in enumerate(extra_lines):
        cv2.putText(img, ln, (10, 60+i*28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,200,0), 1)
    cv2.imwrite(path, img)

# ── ROS shared state ───────────────────────────────────────────────────────────
_xyz_event = threading.Event()
_xyz_msg   = None
_lock      = threading.Lock()

def xyz_cb(msg):
    global _xyz_msg
    with _lock: _xyz_msg = msg
    _xyz_event.set()

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    rospy.init_node('grasp_calibrator', anonymous=True)
    os.makedirs(DEBUG_OUT, exist_ok=True)

    print("\n" + "═"*62)
    print("  DOFBOT AUTO GRASP CALIBRATOR")
    print("═"*62)

    with open(OFFSET_FILE) as f:
        offset = yaml.safe_load(f)
    hsv_range = read_hsv(HSV_FILE)

    print(f"\n  HSV range : {hsv_range}")
    print(f"  Offsets   : x={offset['x_offset']:+.4f}  y={offset['y_offset']:+.4f}  z={offset['z_offset']:+.4f}")

    kin = rospy.ServiceProxy('get_kinemarics', dofbot_pro_kinemarics)
    print("\n  Waiting for /get_kinemarics …", end='', flush=True)
    kin.wait_for_service(); print(" OK")

    home_pos, home_rpy = fk(kin, INIT_JOINTS)
    print(f"  Home FK : x={home_pos[0]:.4f}  y={home_pos[1]:.4f}  z={home_pos[2]:.4f}")

    rospy.Subscriber('/xyz', Position, xyz_cb, queue_size=1)
    pub = rospy.Publisher('/voice_result', Int8, queue_size=1)
    time.sleep(0.5)

    # ── STEP 1: detect cube from HOME ─────────────────────────────────────────
    print("\n" + "─"*62)
    print("Step 1  Detecting cube from home position …")
    rgb0, depth0 = grab_frame()
    det0 = detect_cube(rgb0, depth0, hsv_range, "HOME")
    if det0 is None:
        print("\n[ERROR] Cannot see the red cube from home position. Check HSV / lighting.")
        return
    cx0, cy0, r0, d0 = det0
    P_cam0    = pixel_to_cam(cx0, cy0, d0)
    P_world0  = cam_to_world(P_cam0, home_pos, home_rpy)   # no offsets
    T_world   = P_world0 + np.array([offset['x_offset'], offset['y_offset'], offset['z_offset']])
    r_xy = math.sqrt(T_world[0]**2 + T_world[1]**2)
    z_cor = (r_xy - 0.181) * 0.2   # matches color_grasp_VC line 100
    ik_target = np.array([T_world[0], T_world[1], T_world[2] + z_cor])

    print(f"  P_world (raw)   : {P_world0}")
    print(f"  IK target T     : {ik_target}  (z incl. correction {z_cor:+.4f})")

    save_annotated(f"{DEBUG_OUT}/calib_home.jpg", rgb0, cx0, cy0, r0,
                   f"HOME d={d0:.3f}m T=({ik_target[0]:.3f},{ik_target[1]:.3f},{ik_target[2]:.3f})")

    # ── STEP 2: trigger grasp ─────────────────────────────────────────────────
    print("\n" + "─"*62)
    print("Step 2  Triggering grasp (data=7, red) …")
    pub.publish(Int8(data=7))
    if not _xyz_event.wait(timeout=20.0):
        print("[ERROR] No /xyz in 20 s. Is color_detect_VC running?"); return
    with _lock: tgt = _xyz_msg
    print(f"  /xyz received: px=({tgt.x:.0f},{tgt.y:.0f}) depth={tgt.z:.4f}m")

    # ── STEP 3: wait for arm to settle, snapshot joints ───────────────────────
    print(f"\nStep 3  Waiting for arm to settle (polls every {STABILITY_POLL}s, max {MAX_WAIT_SECS}s) …")
    # First, give time for IK computation + servo ramp-up
    time.sleep(INITIAL_WAIT_SECS)
    prev_deg  = None
    stable_n  = 0
    elapsed   = INITIAL_WAIT_SECS
    s_deg     = None
    while elapsed < MAX_WAIT_SECS:
        try:
            js = rospy.wait_for_message('/joint_states', JointState, timeout=2.0)
        except Exception:
            break
        curr_deg = rad_to_servo(js.position)
        if prev_deg is not None:
            max_chg = max(abs(c - p) for c, p in zip(curr_deg, prev_deg))
            if max_chg < STABILITY_DEG:
                stable_n += 1
                print(f"  t={elapsed:.1f}s  joints stable #{stable_n}/{STABILITY_RUNS}  max_Δ={max_chg:.2f}°")
                if stable_n >= STABILITY_RUNS:
                    s_deg = curr_deg
                    break
            else:
                stable_n = 0
                print(f"  t={elapsed:.1f}s  still moving  max_Δ={max_chg:.2f}°  J={[f'{d:.0f}' for d in curr_deg[:5]]}")
        else:
            print(f"  t={elapsed:.1f}s  first reading: {[f'{d:.0f}' for d in curr_deg[:5]]}")
        prev_deg = curr_deg
        time.sleep(STABILITY_POLL)
        elapsed += STABILITY_POLL

    if s_deg is None:
        s_deg = prev_deg or rad_to_servo(rospy.wait_for_message('/joint_states', JointState, timeout=3.0).position)
        print(f"  [WARN] Stability timeout — using last reading.")

    G_pos, G_rpy = fk(kin, s_deg[:5])
    ik_err = G_pos - ik_target
    print(f"  Final joints (°): {[f'{d:.1f}' for d in s_deg[:5]]}")
    print(f"  Gripper FK  G   : x={G_pos[0]:.4f}  y={G_pos[1]:.4f}  z={G_pos[2]:.4f}")
    print(f"  IK error (G−T)  : Δx={ik_err[0]:+.4f} Δy={ik_err[1]:+.4f} Δz={ik_err[2]:+.4f}  ({np.linalg.norm(ik_err)*100:.1f} cm)")

    # ── STEP 4: re-detect from grasp position ─────────────────────────────────
    print("\nStep 4  Re-detecting cube from grasp position …")
    rgb1, depth1 = grab_frame()
    # Use larger min_r=25 to reject arm-reflection false positives
    det1 = detect_cube(rgb1, depth1, hsv_range, "GRASP", min_r=25)

    P_world1 = None
    d1_note  = ""
    if det1 is not None:
        cx1, cy1, r1, d1 = det1
        if d1 > 0.01:   # valid depth
            P_cam1   = pixel_to_cam(cx1, cy1, d1)
            P_world1 = cam_to_world(P_cam1, G_pos, G_rpy)
            d1_note  = f"d={d1:.3f}m"
            save_annotated(f"{DEBUG_OUT}/calib_grasp.jpg", rgb1, cx1, cy1, r1,
                f"GRASP cube=({P_world1[0]:.3f},{P_world1[1]:.3f},{P_world1[2]:.3f})",
                extra_lines=[f"grip=({G_pos[0]:.3f},{G_pos[1]:.3f},{G_pos[2]:.3f})"])
        else:
            # Depth = 0 AND blob large enough: arm IS essentially at the cube
            d1_note = f"depth=0 r={r1:.0f}px → arm at cube"
            print(f"  Depth=0 and r={r1:.0f}px (large blob) → arm IS at cube. Using G_pos as cube.")
            P_world1 = G_pos.copy()
            save_annotated(f"{DEBUG_OUT}/calib_grasp.jpg", rgb1, cx1, cy1, r1,
                f"GRASP depth=0 grip=({G_pos[0]:.3f},{G_pos[1]:.3f},{G_pos[2]:.3f})")
    else:
        # Cube not visible at all — still save the raw frame for diagnosis
        cv2.imwrite(f"{DEBUG_OUT}/calib_grasp.jpg", rgb1)
        print("  Cube not visible from grasp position (occluded by arm?).")
        print(f"  Saved raw frame to {DEBUG_OUT}/calib_grasp.jpg")

    # ── STEP 5: report ────────────────────────────────────────────────────────
    print("\n" + "═"*62)
    print("  CALIBRATION REPORT")
    print("═"*62)
    print(f"  IK target T    = {ik_target}")
    print(f"  Actual grip G  = {G_pos}")
    print(f"  IK error G−T   = {ik_err}  ({np.linalg.norm(ik_err)*100:.1f} cm)")

    if P_world1 is not None:
        delta = P_world1 - ik_target
        new_off = {
            'x_offset': float(offset['x_offset'] + delta[0]),
            'y_offset': float(offset['y_offset'] + delta[1]),
            'z_offset': float(offset['z_offset'] + delta[2]),
        }
        print(f"\n  Cube est  P₁   = {P_world1}   [{d1_note}]")
        print(f"  Δoffset P₁−T   = {delta}  ({np.linalg.norm(delta)*100:.1f} cm)")
        print(f"\n  Proposed new offsets:")
        for k, v in new_off.items():
            print(f"    {k}: {v:+.6f}  (was {offset[k]:+.6f})")

        if np.linalg.norm(delta) < 0.003:
            print("\n  ✓ Offset error < 3 mm — calibration is already good!")
        else:
            ans = input("\n  Apply corrected offsets? [y/N]: ").strip().lower()
            if ans == 'y':
                with open(OFFSET_FILE, 'w') as f:
                    yaml.dump(new_off, f)
                print(f"  ✓ Saved to {OFFSET_FILE}")
                print("  ➜ Restart color_grasp_VC.py to apply.")
            else:
                print("  Not applied.")
    else:
        print("\n  ⚠ Could not estimate cube world position from grasp frame.")
        print(f"  IK solver error is {np.linalg.norm(ik_err)*100:.1f} cm.")
        print(f"  Debug frames: {DEBUG_OUT}/calib_home.jpg  calib_grasp.jpg")

    print(f"\n  Images saved to: {DEBUG_OUT}/")
    print("═"*62 + "\n")

if __name__ == '__main__':
    main()
