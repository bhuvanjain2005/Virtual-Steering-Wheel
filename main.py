"""
Virtual Steering Wheel - Universal Input Edition (Windows)

One webcam controller with two output modes:
  INPUT_MODE = "gamepad"  -> virtual Xbox 360 controller (analog steering + triggers)
  INPUT_MODE = "keyboard" -> keyboard controls (fallback)

Gestures:
- Rotate the line between your wrists: analog steering
- Right-hand thumbs-up: accelerate (right trigger / configured key)
- Left-hand thumbs-up: brake (left trigger / configured key)
- Press C in preview: calibrate straight ahead
- Press Q in preview: quit

IMPORTANT:
- Gamepad mode requires the optional vgamepad package and ViGEmBus driver.
- ViGEmBus is retired/upstream archived. Use only if comfortable installing a
  system-level driver; compatibility with future Windows versions is not guaranteed.
- No software can guarantee compatibility with every game or anti-cheat system.
"""

import math
import time

import cv2
import mediapipe as mp
import pyautogui

# ----------------------------- SETTINGS -----------------------------

CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# Choose "gamepad" for analog Xbox controller output or "keyboard" for fallback.
INPUT_MODE = "gamepad"

# Keyboard fallback bindings
KEY_LEFT = "left"
KEY_RIGHT = "right"
KEY_ACCELERATE = "up"
KEY_BRAKE = "down"

# Steering tuning
STEERING_DEADZONE_DEG = 5.0
MAX_STEERING_DEG = 35.0
STEERING_SMOOTHING = 0.35
INVERT_STEERING = False
GESTURE_HOLD_SECONDS = 0.10

# Set True if your game sees the virtual controller twice or has input conflicts.
# Do not enable unless you have a separate physical controller to hide.
SHOW_CAMERA_MIRRORED = True

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.0

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def is_thumb_up(hand_landmarks):
    lm = hand_landmarks.landmark
    thumb_extended = lm[4].y < lm[3].y
    other_fingers_folded = (
        lm[8].y > lm[6].y
        and lm[12].y > lm[10].y
        and lm[16].y > lm[14].y
        and lm[20].y > lm[18].y
    )
    return thumb_extended and other_fingers_folded


def get_hand_data(results):
    hands = {}
    if not results.multi_hand_landmarks or not results.multi_handedness:
        return hands
    for landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
        label = handedness.classification[0].label
        wrist = landmarks.landmark[0]
        hands[label] = (landmarks, (wrist.x, wrist.y))
    return hands


class KeyboardOutput:
    def __init__(self):
        self.held = set()

    def update(self, steering, accel, brake):
        desired = set()
        if steering < -0.12:
            desired.add(KEY_LEFT)
        elif steering > 0.12:
            desired.add(KEY_RIGHT)
        if accel:
            desired.add(KEY_ACCELERATE)
        if brake:
            desired.add(KEY_BRAKE)

        for key in self.held - desired:
            try:
                pyautogui.keyUp(key)
            except Exception:
                pass
        for key in desired - self.held:
            try:
                pyautogui.keyDown(key)
            except Exception:
                pass
        self.held = desired

    def close(self):
        for key in list(self.held):
            try:
                pyautogui.keyUp(key)
            except Exception:
                pass
        self.held.clear()


class XboxOutput:
    def __init__(self):
        try:
            import vgamepad as vg
        except ImportError as exc:
            raise RuntimeError(
                "Gamepad mode needs vgamepad. Install it with:\n"
                "  .\\.venv\\Scripts\\python.exe -m pip install vgamepad\n"
                "Then approve the ViGEmBus driver installer if Windows asks."
            ) from exc

        self.vg = vg
        try:
            self.pad = vg.VX360Gamepad()
            self.pad.reset()
            self.pad.update()
        except Exception as exc:
            raise RuntimeError(
                "Could not create the virtual Xbox controller. Check that the "
                "ViGEmBus driver is installed and Windows has been restarted if requested."
            ) from exc

    def update(self, steering, accel, brake):
        # XInput stick axis range: -32768 to +32767.
        x_value = int(max(-1.0, min(1.0, steering)) * 32767)
        self.pad.left_joystick(x_value=x_value, y_value=0)

        # Xbox trigger range: 0 to 255.
        self.pad.right_trigger(value=255 if accel else 0)
        self.pad.left_trigger(value=255 if brake else 0)
        self.pad.update()

    def close(self):
        try:
            self.pad.reset()
            self.pad.update()
        except Exception:
            pass


def draw_dashboard(frame, status, steering, calibrated, accel, brake, hands_visible):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (w, 142), (22, 27, 36), -1)
    cv2.line(frame, (0, 142), (w, 142), (65, 75, 90), 2)

    def label(text, pos, scale=0.6, color=(235, 240, 245), thickness=2):
        cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale,
                    color, thickness, cv2.LINE_AA)

    label("VIRTUAL STEERING WHEEL - UNIVERSAL INPUT", (22, 34), 0.72)
    label(f"MODE: {INPUT_MODE.upper()}  |  {status}", (22, 70), 0.58, (60, 235, 160))
    label("CALIBRATED" if calibrated else "PRESS C TO CALIBRATE",
          (22, 108), 0.52, (80, 230, 140) if calibrated else (40, 210, 255))

    mx, my, mw = 490, 92, 330
    cv2.rectangle(frame, (mx, my), (mx + mw, my + 16), (65, 72, 82), -1)
    cv2.line(frame, (mx + mw // 2, my - 8), (mx + mw // 2, my + 24), (240, 240, 240), 2)
    marker = int(mx + (steering + 1) * mw / 2)
    cv2.circle(frame, (max(mx, min(mx + mw, marker)), my + 8), 9, (40, 210, 255), -1)
    label("LEFT", (mx, 130), 0.38)
    label("CENTER", (mx + 140, 130), 0.38)
    label("RIGHT", (mx + 285, 130), 0.38)

    # Throttle/brake bars
    for x, title, active, color in [
        (22, "ACCEL", accel, (40, 190, 100)),
        (190, "BRAKE", brake, (60, 120, 235)),
    ]:
        cv2.rectangle(frame, (x, 162), (x + 145, 198), (55, 62, 72), -1)
        if active:
            cv2.rectangle(frame, (x, 162), (x + 145, 198), color, -1)
        label(f"{title}: {'ON' if active else 'OFF'}", (x + 12, 187), 0.48)

    # Rotating steering wheel
    cx, cy, radius = w - 135, h - 135, 100
    cv2.circle(frame, (cx, cy), radius, (225, 230, 235), 8, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), int(radius * .72), (90, 100, 110), 2, cv2.LINE_AA)
    angle = steering * 35.0
    for base_angle in (-90, 30, 150):
        a = math.radians(base_angle + angle)
        p1 = (int(cx + math.cos(a) * radius * .18),
              int(cy + math.sin(a) * radius * .18))
        p2 = (int(cx + math.cos(a) * radius * .88),
              int(cy + math.sin(a) * radius * .88))
        cv2.line(frame, p1, p2, (40, 210, 255), 8, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), 18, (40, 210, 255), -1, cv2.LINE_AA)
    label("VIRTUAL WHEEL", (cx - 83, h - 14), 0.40)

    label("C: calibrate   Q: quit   |   Right thumb: accelerate   |   Left thumb: brake",
          (22, h - 20), 0.43, (235, 235, 235), 1)

    if not hands_visible:
        cv2.rectangle(frame, (w // 2 - 165, h // 2 - 32),
                      (w // 2 + 165, h // 2 + 32), (25, 25, 25), -1)
        label("SHOW BOTH HANDS", (w // 2 - 132, h // 2 + 8),
              0.65, (40, 210, 255), 2)


def main():
    if INPUT_MODE.lower() == "gamepad":
        output = XboxOutput()
    elif INPUT_MODE.lower() == "keyboard":
        output = KeyboardOutput()
    else:
        raise ValueError('INPUT_MODE must be "gamepad" or "keyboard".')

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    if not cap.isOpened():
        output.close()
        raise RuntimeError("Could not open webcam. Try CAMERA_INDEX = 1.")

    neutral_angle = None
    smoothed_angle = None
    steering = 0.0
    accel_since = None
    brake_since = None

    print(f"\nVirtual Steering Wheel running in {INPUT_MODE.upper()} mode.")
    print("Show both hands, hold straight, press C to calibrate.")
    print("Select the virtual Xbox controller in your racing game's controls.")
    print("Press Q in the camera window to quit.\n")

    try:
        with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.60,
        ) as hands_model:

            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if SHOW_CAMERA_MIRRORED:
                    frame = cv2.flip(frame, 1)

                results = hands_model.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                hand_data = get_hand_data(results)
                if results.multi_hand_landmarks:
                    for hand_lm in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)

                hands_visible = "Left" in hand_data and "Right" in hand_data
                accel_active = False
                brake_active = False
                status = "SHOW BOTH HANDS"

                if hands_visible:
                    _, (lx, ly) = hand_data["Left"]
                    _, (rx, ry) = hand_data["Right"]
                    if abs(rx - lx) > 0.08:
                        raw_angle = math.degrees(math.atan2(ry - ly, rx - lx))
                        if smoothed_angle is None:
                            smoothed_angle = raw_angle
                        else:
                            smoothed_angle = (
                                STEERING_SMOOTHING * raw_angle
                                + (1 - STEERING_SMOOTHING) * smoothed_angle
                            )

                        if neutral_angle is None:
                            steering = 0.0
                            status = "PRESS C TO CALIBRATE"
                        else:
                            delta = smoothed_angle - neutral_angle
                            if INVERT_STEERING:
                                delta *= -1
                            if abs(delta) <= STEERING_DEADZONE_DEG:
                                delta = 0.0
                            else:
                                delta = math.copysign(
                                    abs(delta) - STEERING_DEADZONE_DEG, delta
                                )
                            steering = max(-1.0, min(1.0, delta / MAX_STEERING_DEG))
                            status = "STEERING LEFT" if steering < -0.05 else (
                                "STEERING RIGHT" if steering > 0.05 else "STRAIGHT"
                            )

                        now = time.time()
                        if is_thumb_up(hand_data["Right"][0]):
                            accel_since = accel_since or now
                        else:
                            accel_since = None
                        if is_thumb_up(hand_data["Left"][0]):
                            brake_since = brake_since or now
                        else:
                            brake_since = None

                        accel_active = (
                            accel_since is not None
                            and now - accel_since >= GESTURE_HOLD_SECONDS
                        )
                        brake_active = (
                            brake_since is not None
                            and now - brake_since >= GESTURE_HOLD_SECONDS
                        )
                    else:
                        status = "MOVE HANDS FARTHER APART"
                        steering = 0.0
                        accel_since = brake_since = None
                else:
                    steering = 0.0
                    smoothed_angle = None
                    accel_since = brake_since = None

                # Fail-safe: if either hand disappears, all controls return to neutral.
                if not hands_visible:
                    accel_active = brake_active = False

                output.update(steering, accel_active, brake_active)
                draw_dashboard(
                    frame, status, steering, neutral_angle is not None,
                    accel_active, brake_active, hands_visible
                )
                cv2.imshow("Virtual Steering Wheel - Universal Input | C calibrate | Q quit", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("c"):
                    if hands_visible:
                        _, (lx, ly) = hand_data["Left"]
                        _, (rx, ry) = hand_data["Right"]
                        neutral_angle = math.degrees(math.atan2(ry - ly, rx - lx))
                        smoothed_angle = neutral_angle
                        steering = 0.0
                        print(f"Calibrated at {neutral_angle:.1f} degrees.")
                    else:
                        print("Show both hands to calibrate.")

    except KeyboardInterrupt:
        pass
    finally:
        output.close()
        cap.release()
        cv2.destroyAllWindows()
        print("Stopped. Controller returned to neutral.")


if __name__ == "__main__":
    main()
