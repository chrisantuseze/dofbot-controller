#!/usr/bin/env python3
"""
verify2act/calibrate_hsv.py
============================
Headless HSV calibration tool — grabs one frame from the camera,
samples the HSV values in a region, and writes recommended HSV ranges
to the color text files.

Usage:
    # Auto-detect from live camera (requires roscore + camera nodes running):
    python3 verify2act/calibrate_hsv.py --color red --from_ros

    # From a saved image:
    python3 verify2act/calibrate_hsv.py --color red --image /path/to/frame.png

    # Show current HSV range and test detection:
    python3 verify2act/calibrate_hsv.py --color red --show_current
"""
import argparse
import sys
import time
import threading
from pathlib import Path
import numpy as np
import cv2

_ROOT = Path(__file__).resolve().parent.parent
_COLOR_DIR = _ROOT / "dofbot_pro_ws/src/dofbot_pro_voice_ctrl/scripts/Color"

# Broader default HSV ranges — good starting points for typical lighting
# Hue wrap: red appears near 0 AND near 180
DEFAULT_RANGES = {
    "red":    [(  0,  60,  60), ( 15, 255, 255)],  # lower red
    "red2":   [(160,  60,  60), (180, 255, 255)],  # upper red (hue wrap)
    "green":  [( 40,  60,  60), ( 85, 255, 255)],
    "blue":   [( 95,  60,  60), (135, 255, 255)],
    "yellow": [( 18,  60,  60), ( 38, 255, 255)],
}

_COLOR_FILE_MAP = {
    "red":    "red_colorHSV.text",
    "green":  "green_colorHSV.text",
    "blue":   "blue_colorHSV.text",
    "yellow": "yellow_colorHSV.text",
}


def write_hsv(color: str, low: tuple, high: tuple):
    path = _COLOR_DIR / _COLOR_FILE_MAP[color]
    line = f"{low[0]}, {low[1]}, {low[2]}, {high[0]}, {high[1]}, {high[2]}"
    path.write_text(line)
    print(f"  Written: {path}")
    print(f"  HSV range: {low} → {high}")


def grab_ros_frame(timeout=10.0):
    """
    Subscribe to /camera/color/image_raw using rospy (native, no rosbridge needed).
    Returns a BGR numpy array or None on timeout.
    """
    try:
        import rospy
        from sensor_msgs.msg import Image
        from cv_bridge import CvBridge
    except ImportError:
        raise ImportError("rospy / cv_bridge not available — are you running on the Jetson?")

    frame_holder = [None]
    ev = threading.Event()
    bridge = CvBridge()

    rospy.init_node("hsv_calibrator", anonymous=True, disable_signals=True)

    def on_image(msg):
        if frame_holder[0] is not None:
            return
        try:
            img = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            img = cv2.flip(img, 0)   # match data_collector convention
            frame_holder[0] = img.copy()
            ev.set()
        except Exception as e:
            print(f"  Frame decode error: {e}")

    sub = rospy.Subscriber("/camera/color/image_raw", Image, on_image, queue_size=1)
    ev.wait(timeout=timeout)
    sub.unregister()
    return frame_holder[0]


def analyse_frame(frame: np.ndarray, color: str):
    """
    Convert to HSV and report statistics of the dominant colored region.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Get the current saved range
    path = _COLOR_DIR / _COLOR_FILE_MAP.get(color, f"{color}_colorHSV.text")
    if path.exists():
        vals = [int(x) for x in path.read_text().split(",")]
        lo = tuple(vals[:3]); hi = tuple(vals[3:])
    else:
        lo, hi = DEFAULT_RANGES[color]

    print(f"\n  Current saved range: {lo} → {hi}")

    # Apply the mask and see how many pixels match
    low = np.array(lo, dtype=np.uint8)
    high = np.array(hi, dtype=np.uint8)
    mask = cv2.inRange(hsv, low, high)
    n = np.count_nonzero(mask)
    total = frame.shape[0] * frame.shape[1]
    print(f"  Pixels matching current range: {n} / {total} ({100*n/total:.1f}%)")

    if n < 200:
        print("\n  *** Too few pixels — colour not detected! ***")
        print("  Suggestions:")
        print("  1. Make sure the cube is visible to the camera")
        print("  2. Run with --write_default to use broader defaults")
        print("  3. Red wrap issue: red may be at H=160-180 instead of H=0-15")

        # Check both ends of red hue
        if color == "red":
            high_red = DEFAULT_RANGES["red2"]
            mask2 = cv2.inRange(hsv,
                                np.array(high_red[0], dtype=np.uint8),
                                np.array(high_red[1], dtype=np.uint8))
            n2 = np.count_nonzero(mask2)
            print(f"\n  Pixels at upper-red range H:160-180: {n2} ({100*n2/total:.1f}%)")
            if n2 > n:
                print("  -> Upper-red range is better! Use --write_default to fix.")
    else:
        print("  Detection looks good — cube is visible.")

    # Overall HSV stats
    print(f"\n  Full frame HSV stats:")
    print(f"    H: mean={h.mean():.0f}  std={h.std():.0f}  min={h.min()}  max={h.max()}")
    print(f"    S: mean={s.mean():.0f}  std={s.std():.0f}")
    print(f"    V: mean={v.mean():.0f}  std={v.std():.0f}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--color", choices=["red","green","blue","yellow"], default="red")
    p.add_argument("--from_ros", action="store_true",
                   help="Grab frame from /camera/color/image_raw via roslibpy")
    p.add_argument("--image", default=None, help="Path to a saved image file")
    p.add_argument("--write_default", action="store_true",
                   help="Write broad default HSV range for this color to file")
    p.add_argument("--show_current", action="store_true",
                   help="Just show the current saved HSV range")
    args = p.parse_args()

    path = _COLOR_DIR / _COLOR_FILE_MAP[args.color]

    if args.show_current:
        if path.exists():
            print(f"Current {args.color} HSV range ({path}):")
            print(" ", path.read_text())
        else:
            print(f"No saved range for {args.color}")
        return

    if args.write_default:
        lo, hi = DEFAULT_RANGES[args.color]
        write_hsv(args.color, lo, hi)
        if args.color == "red":
            # Red wraps — also suggest the upper range
            print(f"\n  NOTE: Red hue wraps in HSV.")
            print(f"  If the cube is not detected, try the upper range:")
            lo2, hi2 = DEFAULT_RANGES["red2"]
            print(f"    python3 verify2act/calibrate_hsv.py --color red --write_upper_red")
        return

    # Load frame
    frame = None
    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"ERROR: could not load image {args.image}")
            sys.exit(1)
        print(f"Loaded image: {args.image} ({frame.shape[1]}x{frame.shape[0]})")
    elif args.from_ros:
        print("Grabbing frame from /camera/color/image_raw …")
        frame = grab_ros_frame()
        if frame is None:
            print("ERROR: No frame received. Is the camera node running?")
            sys.exit(1)
        print(f"Got frame: {frame.shape[1]}x{frame.shape[0]}")
        # Save it for inspection
        out = Path("/tmp/calibration_frame.jpg")
        cv2.imwrite(str(out), frame)
        print(f"Frame saved to {out}")
    else:
        print("No frame source specified. Use --from_ros or --image.")
        print("Showing only current range info:")
        if path.exists():
            print(f"  {args.color}: {path.read_text()}")
        sys.exit(0)

    analyse_frame(frame, args.color)


if __name__ == "__main__":
    main()
