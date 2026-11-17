# Virtual Steering Wheel

Control compatible PC racing games using your laptop webcam and hand gestures. This Windows application uses **MediaPipe** for hand tracking and can send either **virtual Xbox 360/XInput controller input** or **keyboard input**.

> **Project status:** Working prototype tested by the author with GTA V on Windows. Compatibility with other games depends on their controller support, input settings, and anti-cheat restrictions.

## Features

- Webcam-based two-hand tracking with MediaPipe.
- Analog steering using the virtual Xbox controller's left-stick X axis.
- Right-hand thumbs-up gesture for acceleration (right trigger).
- Left-hand thumbs-up gesture for braking (left trigger).
- Keyboard fallback mode.
- Straight-ahead calibration (`C`).
- On-screen camera preview and steering dashboard.
- Releases controller inputs when hand tracking is lost or the application exits.

## How it works

1. OpenCV captures frames from the webcam.
2. MediaPipe detects the left and right hands and tracks their wrist positions.
3. The angle between the wrists is converted into a steering value.
4. Thumbs-up gestures activate acceleration and braking.
5. The selected output backend sends input to Windows as a virtual Xbox controller or keyboard events.

## Requirements

- Windows 10 or Windows 11 (64-bit).
- Python 3.11 (64-bit recommended).
- Webcam.
- A racing game that accepts a standard XInput controller or keyboard input.

### Gamepad mode requirements

Gamepad mode uses [`vgamepad`](https://github.com/yannbouteiller/vgamepad) and the ViGEmBus virtual-device driver.

**Driver maintenance warning:** The upstream ViGEmBus project has been archived/retired. Its driver is a system-level component and may have compatibility or security implications on future Windows versions. Review the official project and release information before installing it. Do not download driver installers from unofficial mirrors. If you do not want to install this driver, use keyboard mode.

## Installation

### 1. Download the repository

Clone it:

```powershell
git clone https://github.com/YOUR-USERNAME/Virtual-Steering-Wheel.git
cd Virtual-Steering-Wheel
```

Or use **Code → Download ZIP** on GitHub and extract the archive.

### 2. Create a Python environment

```powershell
py -3.11 -m venv .venv
```

### 3. Install Python dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Choose an input mode

Open `main.py` and set:

```python
INPUT_MODE = "gamepad"
```

For virtual Xbox controller output, install the optional Python package:

```powershell
.\.venv\Scripts\python.exe -m pip install vgamepad
```

Then follow the official `vgamepad` / ViGEmBus setup instructions. Restart Windows if the driver installer requests it.

For keyboard fallback, change the setting to:

```python
INPUT_MODE = "keyboard"
```

Keyboard mode does not require `vgamepad` or ViGEmBus.

## Run

```powershell
.\.venv\Scripts\python.exe main.py
```

Show both hands to the camera, hold them in a straight-ahead position, and press **C** in the camera preview to calibrate. Press **Q** in the preview to quit.

## Gestures and controls

| Gesture | Gamepad mode | Keyboard mode |
|---|---|---|
| Rotate both wrists left/right | Left stick X axis | Left/right keys |
| Right-hand thumbs-up | Right trigger (RT) | Accelerate key |
| Left-hand thumbs-up | Left trigger (LT) | Brake key |
| Press `C` in preview | Calibrate centre | Calibrate centre |
| Press `Q` in preview | Quit and neutralize controls | Quit and release keys |

Acceleration and braking are currently digital on/off gestures, not pressure-sensitive analog triggers.

## Configure a racing game

1. Start the Python application before launching the game if the game only detects controllers at startup.
2. Open the game's controller/input settings.
3. Enable or select an Xbox 360 / XInput controller, if using gamepad mode.
4. Bind steering to **Left Stick X**, acceleration to **Right Trigger (RT)**, and braking to **Left Trigger (LT)**.
5. If using keyboard mode, bind the keys configured in `main.py`.
6. Test in a low-speed practice area first.

The project does not modify game files. Games differ in how they detect controllers. Some may require manual binding, may not support virtual devices, or may block simulated input. Do not use virtual input where a game's rules prohibit it.

## Configuration

The main settings are near the top of `main.py`:

```python
CAMERA_INDEX = 0
INPUT_MODE = "gamepad"
STEERING_DEADZONE_DEG = 5.0
MAX_STEERING_DEG = 35.0
STEERING_SMOOTHING = 0.35
INVERT_STEERING = False
```

- `CAMERA_INDEX`: use `1` if your webcam is not camera 0.
- `INPUT_MODE`: `"gamepad"` or `"keyboard"`.
- `STEERING_DEADZONE_DEG`: increase to reduce small accidental steering movements.
- `MAX_STEERING_DEG`: adjust how much wrist rotation is needed for full steering.
- `STEERING_SMOOTHING`: lower values are smoother but slower; higher values respond faster.
- `INVERT_STEERING`: set to `True` if steering directions are reversed.

For keyboard mode, edit `KEY_LEFT`, `KEY_RIGHT`, `KEY_ACCELERATE`, and `KEY_BRAKE` in `main.py`.

## Troubleshooting

**Camera does not open**
- Close other apps that may be using the webcam.
- Check Windows camera privacy permissions.
- Try changing `CAMERA_INDEX` from `0` to `1`.

**Hands are not detected reliably**
- Improve room lighting.
- Keep both hands fully inside the camera frame.
- Keep your hands separated and visible.

**Virtual Xbox controller does not appear**
- Confirm that `vgamepad` is installed in this project's `.venv`.
- Check whether the ViGEmBus driver is installed and running.
- Restart Windows if the driver installer requested it.
- Review the driver maintenance warning above.

**Game does not respond**
- Confirm the controller works in Windows' `joy.cpl` Game Controllers panel.
- Ensure the game supports XInput or keyboard input.
- Try starting the Python application before the game.
- Check the game's controller bindings and input-device selection.
- Some games or anti-cheat systems may block virtual input.

## Safety and limitations

- Test in a safe, low-speed in-game area.
- Keep both hands visible; if hand tracking is lost, the application returns controls to neutral.
- Quit the application when not in use.
- This is an experimental accessibility/DIY controller prototype, not a certified gaming peripheral.
- No compatibility guarantee is made for every racing game, launcher, anti-cheat system, or Windows build.

## Contributing

Issues and pull requests are welcome. When reporting a problem, include:
- Windows version.
- Python version.
- Game and launcher.
- Whether you used gamepad or keyboard mode.
- Relevant error messages (remove personal information first).

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
