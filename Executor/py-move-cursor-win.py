import argparse
import ctypes
import time

SendInput = ctypes.windll.user32.SendInput
GetSystemMetrics = ctypes.windll.user32.GetSystemMetrics
GetCursorPos = ctypes.windll.user32.GetCursorPos

SM_CXSCREEN = 0
SM_CYSCREEN = 1

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("mi", MOUSEINPUT)]

def _to_absolute(x, y):
    sx = GetSystemMetrics(SM_CXSCREEN)
    sy = GetSystemMetrics(SM_CYSCREEN)
    ax = int(x * 65535 / max(sx - 1, 1))
    ay = int(y * 65535 / max(sy - 1, 1))
    return ax, ay

def send_mouse_input(dx, dy, flags):
    mi = MOUSEINPUT(dx, dy, 0, flags, 0, None)
    inp = INPUT(INPUT_MOUSE, mi)
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def get_cursor_pos():
    p = POINT()
    GetCursorPos(ctypes.byref(p))
    return p.x, p.y

def move_cursor_smooth(target_x, target_y, duration_ms=3000, steps=30, step_delay=None):
    if step_delay is None:
        step_delay = duration_ms / max(1, steps) / 1000.0

    for i in range(1, steps + 1):
        cx, cy = get_cursor_pos()

        t = i / steps
        t_smooth = t * t * (3 - 2 * t)

        nx = int(round(cx + (target_x - cx) * t_smooth))
        ny = int(round(cy + (target_y - cy) * t_smooth))

        ax, ay = _to_absolute(nx, ny)

        send_mouse_input(ax, ay, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE)
        time.sleep(step_delay)

def double_click():
    send_mouse_input(0, 0, MOUSEEVENTF_LEFTDOWN)
    send_mouse_input(0, 0, MOUSEEVENTF_LEFTUP)
    time.sleep(0.05)
    send_mouse_input(0, 0, MOUSEEVENTF_LEFTDOWN)
    send_mouse_input(0, 0, MOUSEEVENTF_LEFTUP)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-x', '--x', type=int, required=True)
    parser.add_argument('-y', '--y', type=int, required=True)
    parser.add_argument('-d', '--duration_ms', type=float, default=1000, help='movement duration in milliseconds')
    parser.add_argument('-s', '--steps', type=int, default=30, help='number of interpolation steps')
    parser.add_argument('-c', '--click', action='store_true', default=False, help='click after moved')

    args = parser.parse_args()

    x = args.x
    y = args.y
    duration_ms = args.duration_ms
    steps = args.steps
    click = args.click

    move_cursor_smooth(x, y, duration_ms, steps)

    if click:
        double_click()
