#!/usr/bin/env python3
"""
test_gamepad.py — Identify the exact pygame button and axis indices for
                  your USB controller before running gamepad_teleop.py.

Usage:
    python3 scripts/test_gamepad.py           # joystick index 0
    python3 scripts/test_gamepad.py 1         # joystick index 1

Move each stick and press each button once to see its index and value.
Press Ctrl-C to quit.
"""

import os
import sys
import time

# On headless systems (no display), SDL2 must use a dummy video driver so
# that event.pump() actually processes joystick events.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

os.environ["SDL_JOYSTICK_DEVICE"] = "/dev/input/js0" 

import pygame


def main() -> None:
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    pygame.init()
    pygame.joystick.init()

    n = pygame.joystick.get_count()
    if n == 0:
        print("No joystick detected. Is the USB controller plugged in?")
        sys.exit(1)

    if idx >= n:
        print(f"Only {n} joystick(s) found; using index 0.")
        idx = 0

    joy = pygame.joystick.Joystick(idx)
    joy.init()

    print(f"\nController [{idx}]: {joy.get_name()}")
    print(f"  Axes: {joy.get_numaxes()}    Buttons: {joy.get_numbuttons()}\n")
    print("Move sticks / press buttons to see their indices.")
    print("Ctrl-C to quit.\n")

    prev_axes    = [joy.get_axis(i)   for i in range(joy.get_numaxes())]
    prev_buttons = [joy.get_button(i) for i in range(joy.get_numbuttons())]

    try:
        while True:
            pygame.event.pump()

            for i in range(joy.get_numaxes()):
                v = joy.get_axis(i)
                if abs(v - prev_axes[i]) > 0.15:
                    print(f"  AXIS   {i:2d}  value = {v:+.3f}")
                    prev_axes[i] = v

            for i in range(joy.get_numbuttons()):
                b = joy.get_button(i)
                if b != prev_buttons[i]:
                    state = "PRESSED " if b else "released"
                    print(f"  BUTTON {i:2d}  {state}")
                    prev_buttons[i] = b

            time.sleep(0.02)

    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
        print("\nDone.")


if __name__ == "__main__":
    main()
